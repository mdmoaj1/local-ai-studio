from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_plugin_service
from app.schemas.plugins import PluginEnabledPatch, PluginOut
from app.services.plugin_service import PluginService

router = APIRouter()


@router.get("", response_model=list[PluginOut])
async def list_plugins(
    session: AsyncSession = Depends(get_db),
    svc: PluginService = Depends(get_plugin_service),
) -> list[PluginOut]:
    return await svc.list_plugins(session)


@router.patch("/{plugin_id}/enabled", response_model=PluginOut)
async def patch_plugin_enabled(
    plugin_id: int,
    body: PluginEnabledPatch,
    session: AsyncSession = Depends(get_db),
    svc: PluginService = Depends(get_plugin_service),
) -> PluginOut:
    try:
        row = await svc.set_enabled(session, plugin_id, body.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    plugins = await svc.list_plugins(session)
    hit = next((p for p in plugins if p.id == row.id), None)
    if hit is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Plugin list mismatch")
    return hit
