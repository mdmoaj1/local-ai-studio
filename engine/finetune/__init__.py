"""LoRA fine-tuning (Transformers + PEFT).

Reserved for extension: QLoRA, multi-GPU via Accelerate, DeepSpeed JSON configs,
and non-HF weight formats — keep call sites on ``FinetuneService`` / ``JobManager``.
"""

from engine.finetune.lora_trainer import run_lora_training

__all__ = ["run_lora_training"]
