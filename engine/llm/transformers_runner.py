from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Thread
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


class TransformersRunner:
    """Causal LM inference via Hugging Face Transformers (local folder)."""

    def __init__(self) -> None:
        self._tokenizer: AutoTokenizer | None = None
        self._model: Any = None
        self._base_lm: Any = None
        self._device: torch.device | None = None

    def load(self, local_path: Path) -> None:
        path = local_path.resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Model path is not a directory: {path}")

        cuda = torch.cuda.is_available()
        self._device = torch.device("cuda" if cuda else "cpu")
        dtype = torch.float16 if cuda else torch.float32

        self._tokenizer = AutoTokenizer.from_pretrained(str(path), trust_remote_code=True)
        if self._tokenizer.pad_token_id is None and self._tokenizer.eos_token_id is not None:
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id

        load_kwargs: dict = {
            "torch_dtype": dtype,
            "trust_remote_code": True,
        }
        if cuda:
            load_kwargs["device_map"] = "auto"
        else:
            load_kwargs["device_map"] = None

        self._model = AutoModelForCausalLM.from_pretrained(str(path), **load_kwargs)
        if not cuda:
            self._model = self._model.to(self._device)

        self._base_lm = self._model
        self._model.eval()

    def unload(self) -> None:
        if self._model is not None:
            del self._model
        if self._tokenizer is not None:
            del self._tokenizer
        self._model = None
        self._base_lm = None
        self._tokenizer = None
        self._device = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def load_adapter(self, adapter_path: Path) -> None:
        if self._base_lm is None or self._tokenizer is None:
            raise RuntimeError("Model is not loaded")
        from peft import PeftModel

        ap = adapter_path.resolve()
        if not ap.is_dir():
            raise FileNotFoundError(f"Adapter path is not a directory: {ap}")

        if isinstance(self._model, PeftModel):
            if hasattr(self._model, "unload"):
                self._model.unload()
            self._model = self._base_lm

        self._model = PeftModel.from_pretrained(self._base_lm, str(ap))
        self._model.eval()

    @torch.inference_mode()
    def generate(self, prompt: str, *, max_new_tokens: int) -> str:
        if self._tokenizer is None or self._model is None:
            raise RuntimeError("Model is not loaded")

        capped = max(1, min(int(max_new_tokens), 4096))
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if self._device is not None and self._device.type == "cpu":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
        elif self._device is not None and self._device.type == "cuda":
            param_dev = next(self._model.parameters()).device
            if inputs["input_ids"].device != param_dev:
                inputs = {k: v.to(param_dev) for k, v in inputs.items()}

        pad_id = self._tokenizer.pad_token_id
        eos_id = self._tokenizer.eos_token_id

        output_ids = self._model.generate(
            **inputs,
            max_new_tokens=capped,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=pad_id,
            eos_token_id=eos_id,
        )

        in_len = inputs["input_ids"].shape[-1]
        new_tokens = output_ids[0, in_len:]
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        return text.strip()

    @torch.inference_mode()
    def generate_stream(
        self,
        prompt: str,
        *,
        max_new_tokens: int,
        on_chunk: Callable[[str], None],
    ) -> str:
        if self._tokenizer is None or self._model is None:
            raise RuntimeError("Model is not loaded")

        capped = max(1, min(int(max_new_tokens), 4096))
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if self._device is not None and self._device.type == "cpu":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
        elif self._device is not None and self._device.type == "cuda":
            param_dev = next(self._model.parameters()).device
            if inputs["input_ids"].device != param_dev:
                inputs = {k: v.to(param_dev) for k, v in inputs.items()}

        pad_id = self._tokenizer.pad_token_id
        eos_id = self._tokenizer.eos_token_id

        streamer = TextIteratorStreamer(self._tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": capped,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "pad_token_id": pad_id,
            "eos_token_id": eos_id,
        }
        thread = Thread(target=self._model.generate, kwargs=generation_kwargs)
        thread.start()
        parts: list[str] = []
        try:
            for text in streamer:
                parts.append(text)
                on_chunk(text)
        finally:
            thread.join()
        return "".join(parts).strip()
