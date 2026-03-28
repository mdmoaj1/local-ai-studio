from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import app.engine_bootstrap  # noqa: F401

from app.core.config import Settings, get_settings
from app.core.dataset_registry import ensure_under_datasets_root
from app.core.model_registry import ModelStatus, ensure_under_models_root
from app.core.train_progress_hub import train_progress_hub
from app.db.models import AdapterRecord, DatasetRecord, JobRecord, StudioModel
from app.db.session import AsyncSessionLocal
from app.utils.fs import directory_size_bytes
from engine.dataset.loader import load_dataset, split_dataset
from engine.finetune.lora_trainer import run_lora_training
from engine.runtime.scheduler import TrainingThreadScheduler

logger = logging.getLogger(__name__)

_SLUG = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_adapter_slug(name: str) -> str:
    raw = name.strip()
    if not raw:
        return "adapter"
    s = _SLUG.sub("-", raw).strip("-").lower()
    return s or "adapter"


@dataclass(frozen=True)
class LoRAJobSpec:
    job_id: int
    model_id: int
    dataset_id: int
    adapter_name: str
    epochs: int
    learning_rate: float


class JobManager:
    """Background training queue with durable ``jobs`` rows and WebSocket fan-out."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sched = TrainingThreadScheduler()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def shutdown(self) -> None:
        self._sched.shutdown()

    def _run_async(self, coro: Any, timeout: float = 600.0) -> Any:
        loop = self._loop
        if loop is None:
            logger.error("JobManager event loop not configured")
            return None
        fut = asyncio.run_coroutine_threadsafe(coro, loop)
        return fut.result(timeout=timeout)

    async def _update_job(
        self,
        job_id: int,
        *,
        status: str | None = None,
        progress: float | None = None,
        message: str | None = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            row = await session.get(JobRecord, job_id)
            if row is None:
                return
            if status is not None:
                row.status = status
            if progress is not None:
                row.progress = progress
            if message is not None:
                row.message = message
            await session.commit()

    def _emit(self, job_id: int, payload: dict[str, Any]) -> None:
        train_progress_hub.broadcast_threadsafe(job_id, payload)

    def enqueue_lora(self, spec: LoRAJobSpec) -> None:
        settings = self._settings
        loop = self._loop

        def work() -> None:
            if loop is None:
                logger.error("No event loop for training job %s", spec.job_id)
                return
            try:
                self._run_async(
                    self._update_job(spec.job_id, status="running", progress=0.0, message="Starting"),
                    timeout=60.0,
                )
                self._emit(
                    spec.job_id,
                    {"progress": 0.0, "loss": 0.0, "step": 0, "log": "Job running"},
                )

                async def load_ctx() -> tuple[StudioModel, Path, Path, Path, str]:
                    async with AsyncSessionLocal() as session:
                        m = await session.get(StudioModel, spec.model_id)
                        d = await session.get(DatasetRecord, spec.dataset_id)
                        if m is None or d is None:
                            raise ValueError("Model or dataset not found")
                        if m.status != ModelStatus.INSTALLED:
                            raise ValueError("Base model is not installed")
                        base_path = Path(m.local_path).resolve()
                        ds_path = Path(d.path).resolve()
                        root = settings.resolve_models_root()
                        if not ensure_under_models_root(root, base_path):
                            raise ValueError("Invalid base model path")
                        ds_root = settings.resolve_datasets_root()
                        if not ensure_under_datasets_root(ds_root, ds_path):
                            raise ValueError("Invalid dataset path")
                        slug = sanitize_adapter_slug(spec.adapter_name)
                        out = (settings.resolve_adapters_root() / slug).resolve()
                        if not ensure_under_models_root(root, out):
                            raise ValueError("Invalid adapter output path")
                        return m, base_path, ds_path, out, slug

                fut = asyncio.run_coroutine_threadsafe(load_ctx(), loop)
                m_row, base_path, ds_path, out_dir, slug = fut.result(timeout=120)

                records = load_dataset(ds_path)
                train_r, val_r = split_dataset(records, val_ratio=0.1)

                last_loss = 0.0
                last_step = 0

                def on_progress(pct: float, loss: float, step: int) -> None:
                    nonlocal last_loss, last_step
                    last_loss = loss
                    last_step = step
                    self._run_async(
                        self._update_job(
                            spec.job_id,
                            progress=pct,
                            message=f"step={step} loss={loss:.4f}",
                        ),
                        timeout=60.0,
                    )
                    self._emit(
                        spec.job_id,
                        {"progress": pct, "loss": loss, "step": step},
                    )

                def on_log(line: str) -> None:
                    self._emit(spec.job_id, {"log": line})
                    self._run_async(
                        self._update_job(spec.job_id, message=line),
                        timeout=60.0,
                    )

                on_log(f"Base model: {m_row.name} ({base_path})")
                on_log(f"Dataset rows: {len(train_r)} train / {len(val_r)} val")
                mem_line = _cuda_mem_line()
                if mem_line:
                    on_log(mem_line)

                run_lora_training(
                    base_path,
                    train_r,
                    val_r,
                    out_dir,
                    on_progress=on_progress,
                    on_log=on_log,
                    num_train_epochs=max(1, spec.epochs),
                    learning_rate=spec.learning_rate,
                )

                size_b = directory_size_bytes(out_dir)

                async def persist_adapter() -> None:
                    from sqlalchemy import select

                    async with AsyncSessionLocal() as session:
                        res = await session.execute(select(AdapterRecord).where(AdapterRecord.name == slug))
                        prev = res.scalar_one_or_none()
                        if prev:
                            await session.delete(prev)
                        session.add(
                            AdapterRecord(
                                name=slug,
                                path=str(out_dir),
                                base_model=m_row.name,
                                size=size_b,
                            ),
                        )
                        job = await session.get(JobRecord, spec.job_id)
                        if job:
                            job.status = "done"
                            job.progress = 100.0
                            job.message = "Training complete"
                        await session.commit()

                self._run_async(persist_adapter(), timeout=120.0)
                self._emit(
                    spec.job_id,
                    {"done": True, "progress": 100.0, "loss": last_loss, "step": last_step},
                )

            except Exception as exc:
                logger.exception("Training job %s failed", spec.job_id)
                err = str(exc)
                self._run_async(
                    self._update_job(spec.job_id, status="error", message=err),
                    timeout=60.0,
                )
                self._emit(spec.job_id, {"error": err})

        self._sched.submit(work)


def _cuda_mem_line() -> str | None:
    try:
        import torch

        if not torch.cuda.is_available():
            return None
        free_b, total_b = torch.cuda.mem_get_info()
        return (
            f"CUDA memory: free={free_b / (1024**3):.2f} GiB, "
            f"total={total_b / (1024**3):.2f} GiB"
        )
    except Exception:
        return None


_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager(get_settings())
    return _job_manager
