from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download
from tqdm import tqdm

ProgressCallback = Callable[[dict[str, float]], None]


def _make_progress_tqdm(on_progress: ProgressCallback) -> type[tqdm]:
    class ReportingTqdm(tqdm):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._last_emit_at = 0.0
            self._last_n = 0.0
            
            kwargs = {**kwargs}
            kwargs.setdefault("miniters", 1)
            kwargs.setdefault("mininterval", 0.2)
            kwargs.pop("name", None)  # huggingface_hub telemetry kwarg rejects by tqdm
            
            try:
                super().__init__(*args, **kwargs)
            except KeyError:
                # Fallback if huggingface_hub adds more unexpected kwargs
                safe_kwargs = {k: v for k, v in kwargs.items() if k in ["total", "desc", "unit", "unit_scale", "leave", "position", "miniters", "mininterval"]}
                super().__init__(*args, **safe_kwargs)

        def update(self, n: float = 1) -> bool | None:
            res = super().update(n)
            self._maybe_emit()
            return res

        def close(self, *args: Any, **kwargs: Any) -> None:
            self._maybe_emit(force=True)
            super().close(*args, **kwargs)

        def _maybe_emit(self, force: bool = False) -> None:
            now = time.monotonic()
            if not force and (now - self._last_emit_at) < 0.15:
                return
            total_attr = getattr(self, "total", None)
            total = float(total_attr) if total_attr is not None else 0.0
            n_attr = getattr(self, "n", 0)
            downloaded = float(n_attr)
            progress = (downloaded / total * 100.0) if total > 0 else 0.0
            dt = now - self._last_emit_at if self._last_emit_at else 0.0
            dn = downloaded - self._last_n
            speed = (dn / dt) if dt > 0 else 0.0
            self._last_emit_at = now
            self._last_n = downloaded
            on_progress(
                {
                    "progress": min(100.0, max(0.0, progress)),
                    "speed": max(0.0, speed),
                    "downloaded": downloaded,
                    "total": total,
                },
            )

    return ReportingTqdm


class HuggingFaceDownloadService:
    def snapshot_to_directory(
        self,
        *,
        repo_id: str,
        local_dir: Path,
        revision: str | None,
        on_progress: ProgressCallback,
        hf_token: str | None,
    ) -> str:
        local_dir.mkdir(parents=True, exist_ok=True)
        tqdm_cls = _make_progress_tqdm(on_progress)
        return snapshot_download(
            repo_id=repo_id,
            revision=revision,
            local_dir=str(local_dir),
            local_dir_use_symlinks=False,
            tqdm_class=tqdm_cls,
            max_workers=4,
            token=hf_token,
        )
