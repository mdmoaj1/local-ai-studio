from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugin_manager import DiscoveredPlugin, PluginManager
from app.db.models import PluginRecord
from app.schemas.plugins import PluginOut


class PluginService:
    def __init__(self, manager: PluginManager | None = None) -> None:
        self._mgr = manager or PluginManager()

    @property
    def manager(self) -> PluginManager:
        return self._mgr

    async def sync_from_disk(self, session: AsyncSession) -> None:
        discovered = self._mgr.discover()
        for d in discovered:
            stmt = select(PluginRecord).where(PluginRecord.name == d.name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                session.add(
                    PluginRecord(
                        name=d.name,
                        enabled=True,
                        path=d.relative_path,
                    ),
                )
            else:
                row.path = d.relative_path
        await session.commit()

    async def list_plugins(self, session: AsyncSession) -> list[PluginOut]:
        meta: dict[str, DiscoveredPlugin] = {d.name: d for d in self._mgr.discover()}
        stmt = select(PluginRecord).order_by(PluginRecord.name)
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        out: list[PluginOut] = []
        for r in rows:
            d = meta.get(r.name)
            title = d.title if d else r.name
            desc = d.description if d else ""
            out.append(
                PluginOut(
                    id=r.id,
                    name=r.name,
                    title=title,
                    description=desc,
                    enabled=r.enabled,
                    path=r.path,
                ),
            )
        return out

    async def set_enabled(self, session: AsyncSession, plugin_pk: int, enabled: bool) -> PluginRecord:
        row = await session.get(PluginRecord, plugin_pk)
        if row is None:
            raise ValueError("Plugin not found")
        row.enabled = enabled
        await session.commit()
        await session.refresh(row)
        return row

    async def compose_prompt(self, session: AsyncSession, plugin_pk: int, user_text: str) -> str:
        row = await session.get(PluginRecord, plugin_pk)
        if row is None:
            raise ValueError("Plugin not found")
        if not row.enabled:
            raise ValueError("Plugin is disabled")
        plugin = self._mgr.load_plugin(row.path, row.name)
        return plugin.build_prompt(user_text)


_plugin_service_singleton: PluginService | None = None


def get_plugin_service() -> PluginService:
    global _plugin_service_singleton
    if _plugin_service_singleton is None:
        _plugin_service_singleton = PluginService()
    return _plugin_service_singleton
