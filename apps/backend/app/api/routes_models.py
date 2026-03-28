"""Model registry and management API routes.

Existing endpoints (UNCHANGED):
    GET  /api/v1/models            — all DB rows (backward compat)
    POST /api/v1/models/add        — register a custom HF repo
    POST /api/v1/models/download   — start HF snapshot download
    POST /api/v1/models/delete     — remove model from DB + disk

New endpoints:
    GET  /api/v1/models/available  — curated list from registry.json
    GET  /api/v1/models/installed  — only status=installed DB rows
    GET  /api/v1/models/all        — merged registry + DB view
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_model_service
from app.schemas.hf_models import (
    MergedModelOut,
    ModelCreateRequest,
    ModelDownloadRequest,
    ModelIdRequest,
    ModelOut,
    RegistryModelOut,
)
from app.services.model_service import ModelService

router = APIRouter()


# ---------------------------------------------------------------------------
# Existing routes
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ModelOut])
async def get_models(
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> list[ModelOut]:
    rows = await model_service.list_models(session)
    return [ModelOut.model_validate(r) for r in rows]


@router.post("/add", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
async def add_model(
    payload: ModelCreateRequest,
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> ModelOut:
    try:
        row = await model_service.add_model(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ModelOut.model_validate(row)


@router.post("/download", response_model=ModelOut)
async def download_model(
    payload: ModelDownloadRequest,
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> ModelOut:
    try:
        row = await model_service.start_download(session, payload.model_id, payload.revision)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ModelOut.model_validate(row)


@router.post("/delete")
async def delete_model(
    payload: ModelIdRequest,
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> dict[str, bool]:
    try:
        await model_service.delete_model(session, payload.model_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"ok": True}


# ---------------------------------------------------------------------------
# New registry routes
# ---------------------------------------------------------------------------

@router.get("/available", response_model=list[RegistryModelOut])
async def get_available_models(
    model_service: ModelService = Depends(get_model_service),
) -> list[RegistryModelOut]:
    """Return every model defined in models/registry.json (no DB access)."""
    entries = model_service.get_available_models()
    return [
        RegistryModelOut(
            name=e["name"],
            hf_repo=e["hf_repo"],
            type=e["type"],
            runtime=e["runtime"],
            description=e["description"],
        )
        for e in entries
    ]


@router.get("/installed", response_model=list[ModelOut])
async def get_installed_models(
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> list[ModelOut]:
    """Return only models that are fully installed on disk."""
    rows = await model_service.get_installed_models(session)
    return [ModelOut.model_validate(r) for r in rows]


@router.get("/all", response_model=list[MergedModelOut])
async def get_all_models(
    session: AsyncSession = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> list[MergedModelOut]:
    """Return an outer-joined view of registry.json + DB rows.

    - Registry-only entries appear with ``status=not_installed`` and ``id=null``.
    - DB rows for registry entries carry their real status/size.
    - Custom DB rows (not in registry) are appended at the end.
    """
    return await model_service.merge_models(session)
