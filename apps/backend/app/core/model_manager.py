from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import psutil
import torch

import app.engine_bootstrap  # noqa: F401
from app.core.config import Settings
from app.core.model_registry import ensure_under_models_root
from engine.runtime.model_runtime import ModelRuntime


class ModelManager:
    """Single active model policy, load/unload orchestration, coarse memory guard."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._runtime = ModelRuntime()

    @property
    def runtime(self) -> ModelRuntime:
        return self._runtime

    def get_loaded_model_id(self) -> int | None:
        return self._runtime.loaded_model_id

    def get_backend(self) -> str:
        return self._runtime.backend

    def cuda_available(self) -> bool:
        return torch.cuda.is_available()

    def device_label(self) -> str:
        return "cuda" if self.cuda_available() else "cpu"

    def memory_snapshot_mb(self) -> dict[str, float]:
        vm = psutil.virtual_memory()
        out: dict[str, float] = {
            "system_available_mb": vm.available / (1024**2),
            "system_used_percent": vm.percent,
        }
        if self.cuda_available():
            try:
                free_b, total_b = torch.cuda.mem_get_info()
                out["cuda_free_mb"] = free_b / (1024**2)
                out["cuda_total_mb"] = total_b / (1024**2)
            except Exception:
                pass
        return out

    def assert_can_load(self) -> None:
        vm = psutil.virtual_memory()
        if vm.available < 1.5 * 1024**3:
            raise ValueError("Insufficient host RAM to safely load an LLM (need ~1.5 GiB free)")

    def validate_model_path(self, local_path: Path) -> Path:
        resolved = local_path.resolve()
        root = self._settings.resolve_models_root()
        if not ensure_under_models_root(root, resolved):
            raise ValueError("Model path is outside the configured models root")
        if not resolved.is_dir():
            raise ValueError("Model path is not a directory")
        return resolved

    async def load_transformers(self, model_id: int, local_path: Path) -> None:
        self.assert_can_load()
        path = self.validate_model_path(local_path)
        loop = asyncio.get_running_loop()

        def _load() -> None:
            self._runtime.load_transformers(model_id, path)

        await loop.run_in_executor(None, _load)

    async def unload(self) -> None:
        loop = asyncio.get_running_loop()

        def _unload() -> None:
            self._runtime.unload()

        await loop.run_in_executor(None, _unload)

    async def load_adapter(self, adapter_path: Path) -> None:
        path = adapter_path.resolve()
        root = self._settings.resolve_models_root()
        if not ensure_under_models_root(root, path):
            raise ValueError("Adapter path is outside the configured models root")
        if not path.is_dir():
            raise ValueError("Adapter path is not a directory")
        loop = asyncio.get_running_loop()

        def _load() -> None:
            self._runtime.load_adapter(path)

        await loop.run_in_executor(None, _load)

    def generate_sync(self, prompt: str, *, max_tokens: int) -> str:
        return self._runtime.generate(prompt, max_new_tokens=max_tokens)

    def generate_stream_sync(
        self,
        prompt: str,
        *,
        max_tokens: int,
        on_chunk: Callable[[str], None],
    ) -> str:
        return self._runtime.generate_stream(prompt, max_new_tokens=max_tokens, on_chunk=on_chunk)
