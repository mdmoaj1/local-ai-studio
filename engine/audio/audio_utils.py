"""Audio file utilities for the TTS pipeline.

Deliberately dependency-light: only `soundfile` and `pathlib`.
`librosa` is only imported in `convert_audio` which is called rarely.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import soundfile as sf


def save_audio(array, sample_rate: int, out_path: str | Path) -> str:
    """Write a float32 numpy array as a WAV file.

    Parameters
    ----------
    array:
        1-D or 2-D float32 numpy array (samples × channels).
    sample_rate:
        Sample rate in Hz (e.g. 24 000 for most TTS models).
    out_path:
        Destination file path.  Parent dirs are created automatically.

    Returns
    -------
    str
        Absolute path to the written file.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), array, sample_rate, subtype="PCM_16")
    return str(out_path.resolve())


def convert_audio(src: str | Path, dst: str | Path, fmt: str = "wav") -> str:
    """Convert an audio file to a different format.

    Uses `soundfile` for wav↔flac↔ogg round-trips and falls back to a
    raw file copy when the format is the same.

    Parameters
    ----------
    src:
        Source audio file.
    dst:
        Destination audio file (extension should match *fmt*).
    fmt:
        Target format string understood by soundfile (e.g. ``"wav"``,
        ``"flac"``).  mp3 output is not supported by soundfile; for mp3
        use an external tool.

    Returns
    -------
    str
        Absolute path of the output file.
    """
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() == dst.suffix.lower():
        shutil.copy2(src, dst)
        return str(dst.resolve())

    data, sr = sf.read(str(src), always_2d=False, dtype="float32")
    sf.write(str(dst), data, sr, format=fmt.upper())
    return str(dst.resolve())


def get_duration(path: str | Path) -> float:
    """Return duration in seconds of an audio file.

    Parameters
    ----------
    path:
        Path to any audio file supported by soundfile.

    Returns
    -------
    float
        Duration in seconds.  0.0 if the file cannot be read.
    """
    try:
        info = sf.info(str(path))
        return float(info.frames) / info.samplerate
    except Exception:
        return 0.0
