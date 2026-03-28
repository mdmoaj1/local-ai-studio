"""LoRA fine-tuning via Transformers + PEFT.

Extension points (not implemented): QLoRA (bitsandbytes), DeepSpeed config,
multi-GPU via Accelerate / `device_map`, GGUF-native training.
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainerCallback,
    TrainingArguments,
)

logger = logging.getLogger(__name__)

_CANDIDATE_LORA_MODULES = frozenset(
    {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj", "Wqkv", "c_attn", "c_proj"},
)


def _target_modules_for_model(model: torch.nn.Module) -> list[str]:
    found: set[str] = set()
    for name, mod in model.named_modules():
        if not isinstance(mod, nn.Linear):
            continue
        leaf = name.rsplit(".", 1)[-1]
        if leaf in _CANDIDATE_LORA_MODULES:
            found.add(leaf)
    return sorted(found) if found else ["q_proj", "v_proj"]


OnProgress = Callable[[float, float, int], None]
OnLog = Callable[[str], None]


class _ProgressCallback(TrainerCallback):
    def __init__(self, on_progress: OnProgress, on_log: OnLog) -> None:
        self._on_progress = on_progress
        self._on_log = on_log
        self._max_steps: int | None = None

    def on_train_begin(self, args: TrainingArguments, state: Any, control: Any, **kw: Any) -> None:
        self._max_steps = int(state.max_steps) if state.max_steps and state.max_steps > 0 else None

    def on_log(self, args: TrainingArguments, state: Any, control: Any, logs: dict | None = None, **kw: Any) -> None:
        if not logs:
            return
        loss = logs.get("loss")
        step = int(state.global_step)
        if self._max_steps:
            pct = min(100.0, (step / float(self._max_steps)) * 100.0)
        else:
            pct = min(99.0, float(step))
        if loss is not None:
            self._on_progress(pct, float(loss), step)
        if torch.cuda.is_available():
            try:
                alloc = torch.cuda.memory_allocated() / (1024**3)
                peak = torch.cuda.max_memory_allocated() / (1024**3)
                self._on_log(f"GPU memory: allocated={alloc:.2f} GiB, peak={peak:.2f} GiB")
            except Exception:
                pass


def run_lora_training(
    base_model_path: Path,
    train_rows: list[dict[str, str]],
    val_rows: list[dict[str, str]],
    output_path: Path,
    *,
    on_progress: OnProgress,
    on_log: OnLog,
    num_train_epochs: int = 1,
    learning_rate: float = 2e-4,
    per_device_train_batch_size: int = 1,
    gradient_accumulation_steps: int = 4,
    max_seq_length: int = 512,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    warmup_ratio: float = 0.03,
    seed: int = 42,
) -> None:
    """Train a LoRA adapter and write PEFT artifacts to ``output_path``."""
    base_model_path = base_model_path.resolve()
    output_path = output_path.resolve()
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    _ = val_rows  # reserved for eval loops / QLoRA validation

    cuda = torch.cuda.is_available()
    dtype = torch.float16 if cuda else torch.float32

    tok = AutoTokenizer.from_pretrained(str(base_model_path), trust_remote_code=True)
    if tok.pad_token_id is None and tok.eos_token_id is not None:
        tok.pad_token_id = tok.eos_token_id

    load_kw: dict[str, Any] = {"torch_dtype": dtype, "trust_remote_code": True}
    if cuda:
        load_kw["device_map"] = "auto"
    else:
        load_kw["device_map"] = None

    model = AutoModelForCausalLM.from_pretrained(str(base_model_path), **load_kw)
    if not cuda:
        model = model.to(torch.device("cpu"))

    lora = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=_target_modules_for_model(model),
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()
    on_log("LoRA attached; starting tokenization")

    def _format_batch(examples: dict[str, list]) -> dict[str, Any]:
        texts = [
            f"### Prompt:\n{p}\n### Response:\n{r}"
            for p, r in zip(examples["prompt"], examples["response"], strict=True)
        ]
        batch = tok(
            texts,
            truncation=True,
            max_length=max_seq_length,
            padding="max_length",
        )
        batch["labels"] = [[int(x) for x in ids] for ids in batch["input_ids"]]
        return batch

    raw_train = Dataset.from_list(train_rows)
    tokenized_train = raw_train.map(_format_batch, batched=True, remove_columns=raw_train.column_names)

    collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

    args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=float(num_train_epochs),
        per_device_train_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
        logging_steps=1,
        save_strategy="no",
        eval_strategy="no",
        report_to=[],
        fp16=cuda,
        bf16=False,
        seed=seed,
        remove_unused_columns=False,
        load_best_model_at_end=False,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized_train,
        eval_dataset=None,
        data_collator=collator,
        tokenizer=tok,
        callbacks=[_ProgressCallback(on_progress, on_log)],
    )

    on_log("Training started")
    trainer.train()
    trainer.save_model(str(output_path))
    tok.save_pretrained(str(output_path))
    on_log(f"Adapter saved to {output_path}")
