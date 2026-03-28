from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.job_manager import LoRAJobSpec, get_job_manager, sanitize_adapter_slug
from app.db.models import AdapterRecord, DatasetRecord, JobRecord, StudioModel


class FinetuneService:
    async def start_lora(
        self,
        session: AsyncSession,
        *,
        model_id: int,
        dataset_id: int,
        adapter_name: str,
        epochs: int = 1,
        learning_rate: float = 2e-4,
    ) -> JobRecord:
        m = await session.get(StudioModel, model_id)
        d = await session.get(DatasetRecord, dataset_id)
        if m is None or d is None:
            raise ValueError("Model or dataset not found")

        slug = sanitize_adapter_slug(adapter_name)

        existing = await session.execute(select(AdapterRecord).where(AdapterRecord.name == slug))
        if existing.scalar_one_or_none() is not None:
            raise ValueError("An adapter with this name already exists")

        payload = json.dumps(
            {
                "model_id": model_id,
                "dataset_id": dataset_id,
                "adapter_name": adapter_name,
                "epochs": epochs,
                "learning_rate": learning_rate,
            },
        )
        job = JobRecord(
            type="lora",
            status="queued",
            progress=0.0,
            message="Queued",
            payload_json=payload,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        spec = LoRAJobSpec(
            job_id=job.id,
            model_id=model_id,
            dataset_id=dataset_id,
            adapter_name=adapter_name,
            epochs=epochs,
            learning_rate=learning_rate,
        )
        get_job_manager().enqueue_lora(spec)
        return job

    async def get_job(self, session: AsyncSession, job_id: int) -> JobRecord | None:
        return await session.get(JobRecord, job_id)


_finetune_singleton: FinetuneService | None = None


def get_finetune_service() -> FinetuneService:
    global _finetune_singleton
    if _finetune_singleton is None:
        _finetune_singleton = FinetuneService()
    return _finetune_singleton
