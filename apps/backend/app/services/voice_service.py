"""Voice management service.

Responsible for:
- Saving uploaded voice audio files to disk.
- Writing the accompanying config.json.
- Persisting VoiceRecord rows in the database.
- Listing and deleting voices.
- Reporting audio duration via audio_utils.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.voice_record import VoiceRecord
from engine.audio.audio_utils import get_duration

logger = logging.getLogger(__name__)

_ALLOWED_EXTS = {".wav", ".mp3", ".flac", ".ogg"}
_DEFAULT_VOICES_ROOT = Path("voices")


def _voices_root() -> Path:
    root = _DEFAULT_VOICES_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


class VoiceService:
    # ------------------------------------------------------------------ #
    # List
    # ------------------------------------------------------------------ #

    async def list_voices(self, session: AsyncSession) -> list[VoiceRecord]:
        result = await session.execute(select(VoiceRecord).order_by(VoiceRecord.created_at.desc()))
        return list(result.scalars().all())

    def get_duration_for(self, voice: VoiceRecord) -> float:
        """Return audio duration in seconds for a VoiceRecord."""
        voice_dir = Path(voice.path)
        for ext in (".wav", ".mp3", ".flac", ".ogg"):
            candidate = voice_dir / f"audio{ext}"
            if candidate.exists():
                return get_duration(candidate)
        return 0.0

    # ------------------------------------------------------------------ #
    # Upload
    # ------------------------------------------------------------------ #

    async def upload_voice(
        self,
        session: AsyncSession,
        name: str,
        file: UploadFile,
    ) -> VoiceRecord:
        if not name.strip():
            raise ValueError("Voice name must not be empty")

        suffix = Path(file.filename or "audio.wav").suffix.lower()
        if suffix not in _ALLOWED_EXTS:
            raise ValueError(f"Unsupported audio format: {suffix}. Allowed: {', '.join(_ALLOWED_EXTS)}")

        # Check for name uniqueness
        existing = await session.execute(
            select(VoiceRecord).where(VoiceRecord.name == name)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"A voice named '{name}' already exists")

        voice_dir = _voices_root() / name
        voice_dir.mkdir(parents=True, exist_ok=True)

        audio_path = voice_dir / f"audio{suffix}"
        content = await file.read()
        audio_path.write_bytes(content)

        # Write config.json
        config = {
            "name": name,
            "original_filename": file.filename,
            "format": suffix.lstrip("."),
        }
        (voice_dir / "config.json").write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )

        row = VoiceRecord(name=name, path=str(voice_dir.resolve()))
        session.add(row)
        await session.commit()
        await session.refresh(row)
        logger.info("Voice '%s' saved to %s", name, voice_dir)
        return row

    # ------------------------------------------------------------------ #
    # Delete
    # ------------------------------------------------------------------ #

    async def delete_voice(self, session: AsyncSession, voice_id: int) -> None:
        row = await session.get(VoiceRecord, voice_id)
        if row is None:
            raise ValueError(f"Voice {voice_id} not found")

        voice_dir = Path(row.path)
        await session.delete(row)
        await session.commit()

        if voice_dir.exists():
            shutil.rmtree(voice_dir, ignore_errors=True)
            logger.info("Deleted voice dir %s", voice_dir)


# Singleton -------------------------------------------------------------------

_voice_singleton: VoiceService | None = None


def get_voice_service() -> VoiceService:
    global _voice_singleton
    if _voice_singleton is None:
        _voice_singleton = VoiceService()
    return _voice_singleton
