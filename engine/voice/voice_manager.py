"""Voice library scanner and validator.

Voices are stored on disk as::

    voices/
        {voice_name}/
            audio.wav   (or audio.mp3)
            config.json

`VoiceManager` is stateless – it operates on the filesystem only.
The backend ``VoiceService`` owns DB persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


_AUDIO_STEMS = ("audio",)
_AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg")


class VoiceInfo(TypedDict):
    name: str
    path: str            # absolute path to the voice directory
    audio_path: str      # absolute path to the audio file
    config: dict


def validate_voice(voice_dir: str | Path) -> str:
    """Return the audio file path if the voice directory is valid.

    Raises ``ValueError`` if the directory is missing or has no audio file.
    """
    voice_dir = Path(voice_dir)
    if not voice_dir.is_dir():
        raise ValueError(f"Voice directory not found: {voice_dir}")

    for stem in _AUDIO_STEMS:
        for ext in _AUDIO_EXTS:
            candidate = voice_dir / f"{stem}{ext}"
            if candidate.exists():
                return str(candidate.resolve())

    raise ValueError(
        f"No audio file (audio.wav / audio.mp3 …) found in {voice_dir}"
    )


def scan_voices(voices_root: str | Path) -> list[VoiceInfo]:
    """Walk *voices_root* and return metadata for every valid voice."""
    voices_root = Path(voices_root)
    if not voices_root.is_dir():
        return []

    results: list[VoiceInfo] = []
    for subdir in sorted(voices_root.iterdir()):
        if not subdir.is_dir():
            continue
        try:
            audio_path = validate_voice(subdir)
        except ValueError:
            continue  # skip malformed directories

        config_file = subdir / "config.json"
        config: dict = {}
        if config_file.exists():
            try:
                with config_file.open("r", encoding="utf-8") as fh:
                    config = json.load(fh)
            except (json.JSONDecodeError, OSError):
                config = {}

        results.append(
            VoiceInfo(
                name=subdir.name,
                path=str(subdir.resolve()),
                audio_path=audio_path,
                config=config,
            )
        )

    return results


class VoiceManager:
    """Thin wrapper around the module-level helpers."""

    def __init__(self, voices_root: str | Path) -> None:
        self._root = Path(voices_root)

    def scan(self) -> list[VoiceInfo]:
        return scan_voices(self._root)

    def validate(self, voice_dir: str | Path) -> str:
        return validate_voice(voice_dir)

    def voice_dir(self, name: str) -> Path:
        return self._root / name
