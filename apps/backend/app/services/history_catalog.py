from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import History
from app.schemas.catalog import HistoryEntryCreate


class HistoryCatalogService:
    async def list_recent(self, session: AsyncSession, limit: int = 50) -> list[History]:
        stmt = select(History).order_by(History.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_entry(self, session: AsyncSession, payload: HistoryEntryCreate) -> History:
        row = History(
            model_id=payload.model_id,
            prompt=payload.prompt,
            response=payload.response,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row
