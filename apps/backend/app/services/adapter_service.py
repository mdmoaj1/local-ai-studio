from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.model_registry import ensure_under_models_root
from app.db.models import AdapterRecord


class AdapterService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def list_adapters(self, session: AsyncSession) -> list[AdapterRecord]:
        res = await session.execute(select(AdapterRecord).order_by(AdapterRecord.created_at.desc()))
        return list(res.scalars().all())

    async def delete(self, session: AsyncSession, adapter_id: int) -> None:
        row = await session.get(AdapterRecord, adapter_id)
        if row is None:
            raise ValueError("Adapter not found")
        p = Path(row.path).resolve()
        root = self._settings.resolve_models_root()
        if p.exists() and ensure_under_models_root(root, p):
            shutil.rmtree(p, ignore_errors=True)
        await session.delete(row)
        await session.commit()

    def validate_adapter_path(self, row: AdapterRecord) -> Path:
        p = Path(row.path).resolve()
        root = self._settings.resolve_models_root()
        if not ensure_under_models_root(root, p):
            raise ValueError("Adapter path is outside the models root")
        if not p.is_dir():
            raise ValueError("Adapter path is not a directory")
        return p


_adapter_singleton: AdapterService | None = None


def get_adapter_service() -> AdapterService:
    global _adapter_singleton
    if _adapter_singleton is None:
        _adapter_singleton = AdapterService(get_settings())
    return _adapter_singleton
