from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.dataset_registry import (
    dataset_storage_dir,
    ensure_under_datasets_root,
    sanitize_dataset_name,
)
from app.db.models import DatasetRecord
from app.utils.fs import directory_size_bytes
from engine.dataset.loader import DatasetValidationError, load_dataset, validate_dataset


class DatasetService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _root(self) -> Path:
        return self._settings.resolve_datasets_root()

    async def list_datasets(self, session: AsyncSession) -> list[DatasetRecord]:
        res = await session.execute(select(DatasetRecord).order_by(DatasetRecord.created_at.desc()))
        return list(res.scalars().all())

    async def add_from_upload(
        self,
        session: AsyncSession,
        *,
        file: UploadFile,
        display_name: str | None,
    ) -> DatasetRecord:
        root = self._root()
        root.mkdir(parents=True, exist_ok=True)

        raw_name = (display_name or "").strip()
        if not raw_name and file.filename:
            raw_name = Path(file.filename).stem
        if not raw_name:
            raw_name = "dataset"

        slug = sanitize_dataset_name(raw_name)
        dest_dir = dataset_storage_dir(self._settings, slug)
        if dest_dir.exists():
            raise ValueError(f"Dataset name already exists: {slug}")

        dest_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename or "data.jsonl").name
        dest_file = (dest_dir / safe_name).resolve()
        try:
            dest_file.relative_to(dest_dir)
        except ValueError as exc:
            raise ValueError("Invalid filename") from exc

        data = await file.read()
        dest_file.write_bytes(data)

        try:
            records = load_dataset(dest_file)
            validate_dataset(records)
        except (DatasetValidationError, OSError, ValueError) as exc:
            shutil.rmtree(dest_dir, ignore_errors=True)
            raise ValueError(str(exc)) from exc

        size_b = directory_size_bytes(dest_dir)
        row = DatasetRecord(name=slug, path=str(dest_file), size=size_b)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def delete(self, session: AsyncSession, dataset_id: int) -> None:
        row = await session.get(DatasetRecord, dataset_id)
        if row is None:
            raise ValueError("Dataset not found")
        p = Path(row.path).resolve()
        root = self._root()
        target = p if p.is_dir() else p.parent
        if target.exists() and ensure_under_datasets_root(root, target):
            shutil.rmtree(target, ignore_errors=True)
        await session.delete(row)
        await session.commit()


_dataset_singleton: DatasetService | None = None


def get_dataset_service() -> DatasetService:
    global _dataset_singleton
    if _dataset_singleton is None:
        _dataset_singleton = DatasetService(get_settings())
    return _dataset_singleton
