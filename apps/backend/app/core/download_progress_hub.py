from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class DownloadProgressHub:
    """Fan-out download progress to WebSocket subscribers (thread-safe scheduling)."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = asyncio.Lock()
        self._connections: dict[int, set[WebSocket]] = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def register(self, model_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.setdefault(model_id, set()).add(websocket)

    async def unregister(self, model_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            bucket = self._connections.get(model_id)
            if not bucket:
                return
            bucket.discard(websocket)
            if not bucket:
                self._connections.pop(model_id, None)

    async def broadcast(self, model_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(model_id, set()))
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                await self.unregister(model_id, ws)

    def broadcast_threadsafe(self, model_id: int, payload: dict[str, Any]) -> None:
        loop = self._loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(model_id, payload), loop)


download_progress_hub = DownloadProgressHub()
