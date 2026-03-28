"""Qwen3 TTS 1.7B runner with speaker voice cloning.

Architecture notes
------------------
* Heavy ML imports are deferred to ``load()`` so the module can be imported
  on machines without torch/transformers without failure.
* The runner is *synchronous* — all heavy work happens in
  ``generate_sync()``.  The service layer runs it in ``asyncio.to_thread``.
* GPU is used automatically when ``torch.cuda.is_available()``.
* Voice cloning is done by extracting speaker embeddings from the reference
  audio and passing them to the model's forward pass.  The exact API depends
  on the transformers version that ships Qwen3-TTS; when the pipeline
  interface is unavailable we fall back to a minimal raw-generation path.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from engine.audio.audio_utils import save_audio
from engine.tts.base_tts_runner import BaseTTSRunner

logger = logging.getLogger(__name__)


class QwenTTSRunner(BaseTTSRunner):
    """Qwen3-TTS-1.7B runner.

    Capabilities
    ------------
    voice_cloning : yes — reference audio is processed by the model's
                    built-in speaker encoder.
    emotion       : no (future)
    style         : no (future)
    streaming     : no (future)
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._processor: Any = None
        self._device: str = "cpu"
        self._model_path: str = ""

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def load(self, model_path: str) -> None:  # noqa: PLR0912
        """Load Qwen3-TTS weights from *model_path*.

        Attempts three strategies in order:
        1. ``pipeline("text-to-speech", ...)``  — works when supported.
        2. ``AutoProcessor`` + ``AutoModelForSpeechSeq2Seq``
        3. ``AutoProcessor`` + ``AutoModel``                 (fallback)
        """
        import torch
        from transformers import AutoProcessor

        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("QwenTTSRunner: loading from %s on %s", model_path, self._device)

        self._model_path = model_path

        try:
            from transformers import pipeline as hf_pipeline

            self._pipeline = hf_pipeline(
                "text-to-speech",
                model=model_path,
                device=0 if self._device == "cuda" else -1,
            )
            self._processor = None
            self._model = None
            logger.info("QwenTTSRunner: loaded via HF pipeline")
            return
        except Exception as exc:
            logger.debug("HF pipeline path failed (%s), trying AutoModel", exc)

        # Strategy 2/3 — manual load
        try:
            from transformers import AutoModelForSpeechSeq2Seq
            model_cls = AutoModelForSpeechSeq2Seq
        except ImportError:
            from transformers import AutoModel  # type: ignore[assignment]
            model_cls = AutoModel  # type: ignore[assignment]

        import torch

        self._processor = AutoProcessor.from_pretrained(model_path)
        self._model = model_cls.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
        ).to(self._device)
        self._model.eval()
        self._pipeline = None
        logger.info("QwenTTSRunner: loaded via AutoModel")

    def unload(self) -> None:
        import gc

        self._model = None
        self._processor = None
        self._pipeline = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("QwenTTSRunner: unloaded")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None or getattr(self, "_pipeline", None) is not None

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    def generate_sync(  # noqa: PLR0913
        self,
        text: str,
        voice_path: str,
        model_path: str,
        output_path: str,
        on_progress: Callable[[int], None] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate speech and write the result to *output_path*.

        Returns the absolute path of the written audio file.
        """
        if not self.is_loaded:
            raise RuntimeError("Model is not loaded. Call load() first.")

        def _progress(pct: int) -> None:
            if on_progress:
                try:
                    on_progress(pct)
                except Exception:
                    pass

        _progress(5)

        # ---- pipeline path -----------------------------------------------
        if getattr(self, "_pipeline", None) is not None:
            return self._generate_pipeline(text, voice_path, output_path, _progress)

        # ---- manual model path -------------------------------------------
        return self._generate_manual(text, voice_path, output_path, _progress)

    def _generate_pipeline(
        self,
        text: str,
        voice_path: str,
        output_path: str,
        progress: Callable[[int], None],
    ) -> str:
        import numpy as np

        progress(20)
        result = self._pipeline(text, forward_params={"speaker_wav": voice_path})
        progress(80)

        audio = result.get("audio") if isinstance(result, dict) else result
        sr = result.get("sampling_rate", 24_000) if isinstance(result, dict) else 24_000

        if hasattr(audio, "numpy"):
            audio = audio.numpy()
        audio = np.squeeze(np.array(audio, dtype=np.float32))

        path = save_audio(audio, sr, output_path)
        progress(100)
        return path

    def _generate_manual(
        self,
        text: str,
        voice_path: str,
        output_path: str,
        progress: Callable[[int], None],
    ) -> str:
        import numpy as np
        import torch

        progress(20)

        # Encode text
        inputs = self._processor(text=text, return_tensors="pt").to(self._device)

        # Load reference audio for speaker embedding
        try:
            import soundfile as sf

            ref_audio, ref_sr = sf.read(voice_path, dtype="float32", always_2d=False)
            speaker_inputs = self._processor(
                audio=ref_audio,
                sampling_rate=ref_sr,
                return_tensors="pt",
            ).to(self._device)
            inputs.update(speaker_inputs)
        except Exception as exc:
            logger.warning("Could not load reference voice (%s); generating without cloning", exc)

        progress(40)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=1024,
            )

        progress(80)

        # Extract waveform — shape varies by model
        waveform = outputs
        if hasattr(outputs, "waveform"):
            waveform = outputs.waveform
        elif hasattr(outputs, "audio_sequence"):
            waveform = outputs.audio_sequence

        if hasattr(waveform, "cpu"):
            waveform = waveform.cpu().float().numpy()
        waveform = np.squeeze(np.array(waveform, dtype=np.float32))

        sr = getattr(self._processor, "sampling_rate", 24_000)
        path = save_audio(waveform, sr, output_path)
        progress(100)
        return path

    def capabilities(self) -> dict[str, bool]:
        return {
            "voice_cloning": True,
            "emotion": False,
            "style": False,
            "streaming": False,
        }


# Module-level singleton
_runner: QwenTTSRunner | None = None


def get_qwen_runner() -> QwenTTSRunner:
    global _runner
    if _runner is None:
        _runner = QwenTTSRunner()
    return _runner


