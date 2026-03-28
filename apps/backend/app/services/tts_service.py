"""TTS Generation Service.

Orchestrates:
1. Resolve voice and model from DB.
2. Lazy-load the TTS runner (Qwen3 or any BaseTTSRunner subclass).
3. Run inference in a thread executor.
4. Save the audio file under outputs/audio/.
5. Persist a TtsHistory row.
6. Broadcast progress via TtsProgressHub.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tts_progress_hub import tts_progress_hub
from app.db.models.studio_model import StudioModel
from app.db.models.tts_history import TtsHistory
from app.db.models.voice_record import VoiceRecord
from app.db.session import AsyncSessionLocal
from engine.audio.audio_utils import get_duration
from engine.tts.qwen_tts_runner import QwenTTSRunner

logger = logging.getLogger(__name__)

_AUDIO_OUTPUT_ROOT = Path("outputs/audio")


def _audio_root() -> Path:
    _AUDIO_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    return _AUDIO_OUTPUT_ROOT


class TTSService:
    """Singleton TTS orchestrator."""

    def __init__(self) -> None:
        # Runner is loaded lazily when the first generation request arrives.
        # This avoids loading GPU model at startup.
        self._runner: QwenTTSRunner | None = None
        self._loaded_model_id: int | None = None

    # ------------------------------------------------------------------ #
    # Runner management
    # ------------------------------------------------------------------ #

    def _ensure_runner(self) -> QwenTTSRunner:
        if self._runner is None:
            self._runner = QwenTTSRunner()
        return self._runner

    async def _load_runner(self, model_path: str, model_id: int) -> None:
        """(Re)load runner if the requested model differs from the loaded one."""
        if self._loaded_model_id == model_id:
            return
        runner = self._ensure_runner()
        if runner.is_loaded:
            await asyncio.to_thread(runner.unload)
        await asyncio.to_thread(runner.load, model_path)
        self._loaded_model_id = model_id

    # ------------------------------------------------------------------ #
    # Generate
    # ------------------------------------------------------------------ #

    async def generate(
        self,
        *,
        text: str,
        voice_id: int,
        model_id: int,
        session: AsyncSession,
    ) -> tuple[str, float, int, str]:
        """Generate TTS audio.

        Returns
        -------
        tuple[audio_url, duration, history_id, job_id]
        """
        job_id = str(uuid.uuid4())

        # ---- resolve DB rows ----
        voice_row = await session.get(VoiceRecord, voice_id)
        if voice_row is None:
            raise ValueError(f"Voice {voice_id} not found")

        model_row = await session.get(StudioModel, model_id)
        if model_row is None:
            raise ValueError(f"Model {model_id} not found")
        if model_row.status != "installed":
            raise ValueError(f"Model '{model_row.name}' is not installed on disk")

        # ---- find voice audio file ----
        voice_dir = Path(voice_row.path)
        voice_audio: Path | None = None
        for ext in (".wav", ".mp3", ".flac", ".ogg"):
            candidate = voice_dir / f"audio{ext}"
            if candidate.exists():
                voice_audio = candidate
                break
        if voice_audio is None:
            raise ValueError(f"No audio file found for voice '{voice_row.name}'")

        # ---- prepare output path ----
        out_filename = f"tts_{job_id}.wav"
        out_path = _audio_root() / out_filename

        # ---- load model ----
        await self._load_runner(model_row.local_path, model_id)
        runner = self._ensure_runner()

        # ---- thread-safe progress callback ----
        def _on_progress(pct: int) -> None:
            tts_progress_hub.broadcast_threadsafe(job_id, {"progress": pct})

        # ---- run inference in executor ----
        fn = functools.partial(
            runner.generate_sync,
            text,
            str(voice_audio),
            model_row.local_path,
            str(out_path),
            _on_progress,
        )
        await asyncio.to_thread(fn)

        duration = get_duration(out_path)

        # ---- persist history ----
        async with AsyncSessionLocal() as hist_session:
            hist_row = TtsHistory(
                text=text,
                voice_id=voice_id,
                model_id=model_id,
                audio_path=str(out_path.resolve()),
            )
            hist_session.add(hist_row)
            await hist_session.commit()
            await hist_session.refresh(hist_row)
            history_id = hist_row.id

        audio_url = f"/audio/{out_filename}"
        logger.info("TTS job %s complete → %s (%.1fs)", job_id, out_filename, duration)
        return audio_url, duration, history_id, job_id

    # ------------------------------------------------------------------ #
    # History
    # ------------------------------------------------------------------ #

    async def list_history(self, session: AsyncSession, limit: int = 50) -> list[TtsHistory]:
        result = await session.execute(
            select(TtsHistory).order_by(TtsHistory.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


# Singleton -------------------------------------------------------------------

_tts_singleton: TTSService | None = None


def get_tts_service() -> TTSService:
    global _tts_singleton
    if _tts_singleton is None:
        _tts_singleton = TTSService()
    return _tts_singleton
