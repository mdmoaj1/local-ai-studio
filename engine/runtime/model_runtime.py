from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from engine.llm.transformers_runner import TransformersRunner

BackendName = Literal["none", "transformers", "gguf", "tts"]


class ModelRuntime:
    """Holds at most one active inference backend in memory."""

    def __init__(self) -> None:
        self._load_lock = threading.Lock()
        self._gen_lock = threading.Lock()
        self._transformers: TransformersRunner | None = None
        self._loaded_model_id: int | None = None
        self._backend: BackendName = "none"

    @property
    def loaded_model_id(self) -> int | None:
        return self._loaded_model_id

    @property
    def backend(self) -> BackendName:
        return self._backend

    def load_transformers(self, model_id: int, local_path: Path) -> None:
        with self._load_lock:
            if self._transformers is not None:
                raise RuntimeError("A model is already loaded; unload it first")
            runner = TransformersRunner()
            runner.load(local_path)
            self._transformers = runner
            self._loaded_model_id = model_id
            self._backend = "transformers"

    def load_gguf(self, _model_id: int, _local_path: Path) -> None:
        raise NotImplementedError("GGUF runtime will mount here (llama.cpp / llama-cpp-python).")

    def load_adapter(self, adapter_path: Path) -> None:
        with self._gen_lock:
            with self._load_lock:
                if self._transformers is None:
                    raise RuntimeError("No Transformers model loaded")
                self._transformers.load_adapter(adapter_path)

    def unload(self) -> None:
        with self._gen_lock:
            with self._load_lock:
                if self._transformers is not None:
                    self._transformers.unload()
                    self._transformers = None
                self._loaded_model_id = None
                self._backend = "none"

    def generate(self, prompt: str, *, max_new_tokens: int) -> str:
        with self._gen_lock:
            if self._transformers is None:
                raise RuntimeError("No Transformers model is loaded")
            return self._transformers.generate(prompt, max_new_tokens=max_new_tokens)

    def generate_stream(
        self,
        prompt: str,
        *,
        max_new_tokens: int,
        on_chunk: Callable[[str], None],
    ) -> str:
        with self._gen_lock:
            if self._transformers is None:
                raise RuntimeError("No Transformers model is loaded")
            return self._transformers.generate_stream(prompt, max_new_tokens=max_new_tokens, on_chunk=on_chunk)
