from __future__ import annotations

import asyncio
import logging
import shutil
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.model_registry import (
    ModelKind,
    ModelStatus,
    RegistryEntry,
    ensure_under_models_root,
    list_available_models,
    model_storage_dir,
)
from app.db.models import StudioModel
from app.schemas.hf_models import MergedModelOut, ModelCreateRequest, RegistryModelOut
from app.services.download_service import HuggingFaceDownloadService
from app.utils.fs import directory_size_bytes
from app.core.ws_manager import download_progress


class ModelService:
    def __init__(
        self,
        settings: Settings,
        download_service: HuggingFaceDownloadService,
    ) -> None:
        self._settings = settings
        self._download = download_service
        self._tasks: dict[int, asyncio.Task[None]] = {}
        self._locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    # ------------------------------------------------------------------ #
    # Existing (unchanged for backward compat)
    # ------------------------------------------------------------------ #

    async def list_models(self, session: AsyncSession) -> list[StudioModel]:
        stmt = select(StudioModel).order_by(StudioModel.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def add_model(self, session: AsyncSession, payload: ModelCreateRequest) -> StudioModel:
        if payload.type not in {k.value for k in ModelKind}:
            raise ValueError("Invalid model type")

        storage_dir = model_storage_dir(self._settings, payload.name)
        models_root = self._settings.resolve_models_root()
        if not ensure_under_models_root(models_root, storage_dir):
            raise ValueError("Invalid model path")

        existing = await session.execute(select(StudioModel).where(StudioModel.name == payload.name))
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Model name already exists")

        row = StudioModel(
            name=payload.name.strip(),
            hf_repo_id=payload.hf_repo_id.strip(),
            local_path=str(storage_dir),
            size=0,
            status=ModelStatus.NOT_INSTALLED,
            model_type=payload.type,
            runtime=payload.runtime,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def delete_model(self, session: AsyncSession, model_id: int) -> None:
        row = await session.get(StudioModel, model_id)
        if row is None:
            raise ValueError("Model not found")

        task = self._tasks.pop(model_id, None)
        if task:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        row = await session.get(StudioModel, model_id)
        if row is None:
            return

        path = Path(row.local_path)
        models_root = self._settings.resolve_models_root()
        if path.exists() and ensure_under_models_root(models_root, path):
            shutil.rmtree(path, ignore_errors=True)

        await session.delete(row)
        await session.commit()

    async def start_download(self, session: AsyncSession, model_id: int, revision: str | None) -> StudioModel:
        async with self._locks[model_id]:
            row = await session.get(StudioModel, model_id)
            if row is None:
                raise ValueError("Model not found")

            active = self._tasks.get(model_id)
            if row.status == ModelStatus.DOWNLOADING and active is not None and not active.done():
                return row

            if row.status == ModelStatus.INSTALLED:
                raise ValueError("Model already installed")
            if row.status not in {ModelStatus.NOT_INSTALLED, ModelStatus.ERROR, ModelStatus.DOWNLOADING}:
                raise ValueError("Model is not downloadable in its current state")

            models_root = self._settings.resolve_models_root()
            storage = Path(row.local_path).resolve()
            if not ensure_under_models_root(models_root, storage):
                raise ValueError("Model path is outside models root")

            usage = psutil.disk_usage(str(models_root))
            if usage.free < 256 * 1024 * 1024:
                raise ValueError("Insufficient disk space (need at least 256 MiB free)")

            row.status = ModelStatus.DOWNLOADING
            row.size = 0
            await session.commit()
            await session.refresh(row)

            if self._tasks.get(model_id) and not self._tasks[model_id].done():
                return row

            self._tasks[model_id] = asyncio.create_task(
                self._download_worker(model_id, revision),
            )
            return row

    async def _download_worker(self, model_id: int, revision: str | None) -> None:
        settings = get_settings()
        from app.db.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as session:
                row = await session.get(StudioModel, model_id)
                if row is None:
                    return
                local_dir = Path(row.local_path).resolve()
                models_root = settings.resolve_models_root()
                if not ensure_under_models_root(models_root, local_dir):
                    row.status = ModelStatus.ERROR
                    await session.commit()
                    return

                def on_progress(payload: dict[str, float]) -> None:
                    # Update progress dict directly (non-blocking)
                    download_progress[model_id] = {
                        "progress": payload["progress"],
                        "speed": payload["speed"],
                        "downloaded": payload["downloaded"],
                        "total": payload["total"],
                        "status": "downloading"
                    }

                loop = asyncio.get_running_loop()

                def run_sync() -> None:
                    self._download.snapshot_to_directory(
                        repo_id=row.hf_repo_id,
                        local_dir=local_dir,
                        revision=revision,
                        on_progress=on_progress,
                        hf_token=settings.hf_token,
                    )

                await loop.run_in_executor(None, run_sync)

                row.size = directory_size_bytes(local_dir)
                row.status = ModelStatus.INSTALLED
                await session.commit()
                
                # Mark done in memory dict
                download_progress[model_id] = {
                    "progress": 100.0,
                    "speed": 0.0,
                    "downloaded": float(row.size),
                    "total": float(row.size),
                    "status": "installed",
                }
        except asyncio.CancelledError:
            download_progress[model_id] = {
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0.0,
                "total": 0.0,
                "status": "error",
            }
            async with AsyncSessionLocal() as session:
                row = await session.get(StudioModel, model_id)
                if row:
                    row.status = ModelStatus.ERROR
                    await session.commit()
            raise
        except Exception as e:
            logger.exception(f"Model download failed for model_id={model_id}: {e}")
            download_progress[model_id] = {
                "progress": 0.0,
                "speed": 0.0,
                "downloaded": 0.0,
                "total": 0.0,
                "status": "error",
            }
            async with AsyncSessionLocal() as session:
                row = await session.get(StudioModel, model_id)
                if row:
                    row.status = ModelStatus.ERROR
                    await session.commit()
        finally:
            self._tasks.pop(model_id, None)

    # ------------------------------------------------------------------ #
    # Registry / merge API (NEW)
    # ------------------------------------------------------------------ #

    def get_available_models(self) -> list[RegistryEntry]:
        """Return every model from registry.json (no DB access needed)."""
        return list_available_models()

    async def get_installed_models(self, session: AsyncSession) -> list[StudioModel]:
        """Return only models whose status is 'installed'."""
        stmt = (
            select(StudioModel)
            .where(StudioModel.status == ModelStatus.INSTALLED)
            .order_by(StudioModel.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def merge_models(self, session: AsyncSession) -> list[MergedModelOut]:
        """Outer-join registry entries with DB rows by hf_repo_id.

        Result set:
        - Registry entry without a DB row → status=not_installed
        - Registry entry with a DB row    → real DB status / size
        - DB row without a registry entry → included as-is (custom adds)
        """
        registry: list[RegistryEntry] = list_available_models()
        all_db: list[StudioModel] = await self.list_models(session)

        # Index DB rows by hf_repo_id for O(1) lookup
        db_by_repo: dict[str, StudioModel] = {r.hf_repo_id: r for r in all_db}
        seen_repo_ids: set[str] = set()

        merged: list[MergedModelOut] = []

        # 1. Walk registry (preserves registry order)
        for entry in registry:
            repo = entry["hf_repo"]
            seen_repo_ids.add(repo)
            db_row = db_by_repo.get(repo)
            if db_row:
                merged.append(
                    MergedModelOut(
                        name=db_row.name,
                        hf_repo=repo,
                        type=db_row.model_type,
                        runtime=db_row.runtime,
                        description=entry["description"],
                        id=db_row.id,
                        status=db_row.status,
                        size=db_row.size,
                        local_path=db_row.local_path,
                    )
                )
            else:
                merged.append(
                    MergedModelOut(
                        name=entry["name"],
                        hf_repo=repo,
                        type=entry["type"],
                        runtime=entry["runtime"],
                        description=entry["description"],
                        id=None,
                        status=ModelStatus.NOT_INSTALLED,
                        size=0,
                        local_path="",
                    )
                )

        # 2. Append DB rows not present in registry (custom user adds)
        for db_row in all_db:
            if db_row.hf_repo_id not in seen_repo_ids:
                merged.append(
                    MergedModelOut(
                        name=db_row.name,
                        hf_repo=db_row.hf_repo_id,
                        type=db_row.model_type,
                        runtime=db_row.runtime,
                        description="",
                        id=db_row.id,
                        status=db_row.status,
                        size=db_row.size,
                        local_path=db_row.local_path,
                    )
                )

        return merged


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_model_service_singleton: ModelService | None = None


def get_model_service() -> ModelService:
    global _model_service_singleton
    if _model_service_singleton is None:
        _model_service_singleton = ModelService(
            settings=get_settings(),
            download_service=HuggingFaceDownloadService(),
        )
    return _model_service_singleton
