"""Abstract base for all TTS engine runners.

Concrete implementations (Qwen3, XTTS, Bark, StyleTTS2 …) subclass this.
Only BaseTTSRunner is imported at the service layer so the service stays
decoupled from any specific backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class BaseTTSRunner(ABC):
    """Interface every TTS runner must satisfy."""

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    @abstractmethod
    def load(self, model_path: str) -> None:
        """Load weights into memory (blocking, call in a thread executor)."""

    @abstractmethod
    def unload(self) -> None:
        """Release model weights and free memory."""

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """True when the model is resident in memory."""

    # ------------------------------------------------------------------ #
    # Inference
    # ------------------------------------------------------------------ #

    @abstractmethod
    def generate_sync(
        self,
        text: str,
        voice_path: str,
        model_path: str,
        output_path: str,
        on_progress: Callable[[int], None] | None = None,
        # Future-ready kwargs — emotion, style, speed, streaming, etc.
        **kwargs: Any,
    ) -> str:
        """Generate speech synchronously.

        Parameters
        ----------
        text:
            Input text to synthesise.
        voice_path:
            Path to the reference speaker audio file (wav/mp3).
        model_path:
            Root directory of the TTS model weights.
        output_path:
            Destination file path (wav).  The runner MUST write the audio
            here and return the same path.
        on_progress:
            Optional callback receiving an integer 0-100.

        Returns
        -------
        str
            Absolute path to the generated audio file.
        """

    # ------------------------------------------------------------------ #
    # Introspection (optional overrides)
    # ------------------------------------------------------------------ #

    @property
    def runner_name(self) -> str:
        return self.__class__.__name__

    def capabilities(self) -> dict[str, bool]:
        """Advertise optional features supported by this runner."""
        return {
            "voice_cloning": False,
            "emotion": False,
            "style": False,
            "streaming": False,
        }
