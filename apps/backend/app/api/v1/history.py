from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_history_catalog_service
from app.schemas.catalog import HistoryEntryCreate, HistoryEntryOut
from app.services.history_catalog import HistoryCatalogService

router = APIRouter()


@router.get("", response_model=list[HistoryEntryOut])
async def list_history(
    session: AsyncSession = Depends(get_db),
    catalog: HistoryCatalogService = Depends(get_history_catalog_service),
) -> list[HistoryEntryOut]:
    rows = await catalog.list_recent(session, limit=20)
    return [HistoryEntryOut.model_validate(r) for r in rows]


@router.post("", response_model=HistoryEntryOut)
async def create_history_entry(
    payload: HistoryEntryCreate,
    session: AsyncSession = Depends(get_db),
    catalog: HistoryCatalogService = Depends(get_history_catalog_service),
) -> HistoryEntryOut:
    row = await catalog.create_entry(session, payload)
    return HistoryEntryOut.model_validate(row)
