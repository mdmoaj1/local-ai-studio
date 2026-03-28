from __future__ import annotations

import re
from pathlib import Path

from app.core.config import Settings

_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_dataset_name(name: str) -> str:
    raw = name.strip()
    if not raw:
        return "unnamed-dataset"
    slug = _SLUG_RE.sub("-", raw).strip("-").lower()
    return slug or "unnamed-dataset"


def dataset_storage_dir(settings: Settings, display_name: str) -> Path:
    root = settings.resolve_datasets_root()
    return (root / sanitize_dataset_name(display_name)).resolve()


def ensure_under_datasets_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False
