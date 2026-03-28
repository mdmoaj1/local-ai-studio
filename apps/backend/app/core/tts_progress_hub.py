"""TTS generation progress hub — mirrors train_progress_hub pattern."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class TtsProgressHub:
    """Fan-out TTS progress events to WebSocket subscribers (thread-safe)."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = asyncio.Lock()
        self._connections: dict[str, set[WebSocket]] = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def register(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.setdefault(job_id, set()).add(websocket)

    async def unregister(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            bucket = self._connections.get(job_id)
            if not bucket:
                return
            bucket.discard(websocket)
            if not bucket:
                self._connections.pop(job_id, None)

    async def broadcast(self, job_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(job_id, set()))
        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                await self.unregister(job_id, ws)

    def broadcast_threadsafe(self, job_id: str, payload: dict[str, Any]) -> None:
        """Call from a worker thread to push progress events into the event loop."""
        loop = self._loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(job_id, payload), loop)


tts_progress_hub = TtsProgressHub()
