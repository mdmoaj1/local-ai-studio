from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from app.core.config import Settings


class ModelStatus(StrEnum):
    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLED = "installed"
    ERROR = "error"


class ModelKind(StrEnum):
    LLM = "llm"
    TTS = "tts"
    VOICE = "voice"
    GGUF = "gguf"


class RuntimeKind(StrEnum):
    TRANSFORMERS = "transformers"
    GGUF = "gguf"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Registry entry — mirrors the shape of registry.json
# ---------------------------------------------------------------------------

class RegistryEntry(TypedDict):
    name: str
    hf_repo: str
    type: str        # "llm" | "tts" | "voice"
    runtime: str     # "transformers" | "gguf" | …
    description: str


# ---------------------------------------------------------------------------
# Path helpers (UNCHANGED — keep for existing callers)
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_model_dir_name(name: str) -> str:
    raw = name.strip()
    if not raw:
        return "unnamed-model"
    slug = _SLUG_RE.sub("-", raw).strip("-").lower()
    return slug or "unnamed-model"


def model_storage_dir(settings: Settings, display_name: str) -> Path:
    root = settings.resolve_models_root()
    return (root / sanitize_model_dir_name(display_name)).resolve()


def ensure_under_models_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Runtime detection
# ---------------------------------------------------------------------------

def detect_runtime(model_dir: str | Path) -> str:
    """Inspect a local model directory and infer its runtime.

    Rules (in priority order):
    1. Any ``*.gguf`` file found   → ``"gguf"``
    2. ``config.json`` present     → ``"transformers"``
    3. Fallback                    → ``"unknown"``
    """
    p = Path(model_dir)
    if not p.is_dir():
        return RuntimeKind.UNKNOWN
    if any(p.glob("*.gguf")):
        return RuntimeKind.GGUF
    if (p / "config.json").exists():
        return RuntimeKind.TRANSFORMERS
    return RuntimeKind.UNKNOWN


# ---------------------------------------------------------------------------
# Registry file loader
# ---------------------------------------------------------------------------

def _registry_path() -> Path:
    """Resolve the monorepo-relative path to ``models/registry.json``.

    File layout: ``apps/backend/app/core/model_registry.py``
    So ``parents[4]`` is the repo root.
    """
    return (Path(__file__).resolve().parents[4] / "models" / "registry.json").resolve()


def load_registry() -> list[RegistryEntry]:
    """Read and parse ``models/registry.json``.

    Returns an empty list on any read / parse error so the app never
    crashes due to a missing or malformed registry file.
    """
    path = _registry_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        raw: list[dict] = data.get("models", [])
        entries: list[RegistryEntry] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            entry: RegistryEntry = {
                "name": str(item.get("name", "")),
                "hf_repo": str(item.get("hf_repo", "")),
                "type": str(item.get("type", "llm")),
                "runtime": str(item.get("runtime", "transformers")),
                "description": str(item.get("description", "")),
            }
            if entry["name"] and entry["hf_repo"]:
                entries.append(entry)
        return entries
    except (OSError, json.JSONDecodeError, KeyError):
        return []


def list_available_models() -> list[RegistryEntry]:
    """Public alias: return every entry from the registry catalogue."""
    return load_registry()
