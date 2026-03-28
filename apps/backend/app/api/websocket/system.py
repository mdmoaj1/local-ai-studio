import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.services.system_service import SystemService

router = APIRouter()


@router.websocket("/ws/system")
async def system_metrics_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    settings = get_settings()
    svc = SystemService()
    try:
        while True:
            snap = svc.snapshot()
            payload: dict[str, Any] = snap.as_ws_payload()
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(settings.system_ws_interval_seconds)
    except WebSocketDisconnect:
        return
