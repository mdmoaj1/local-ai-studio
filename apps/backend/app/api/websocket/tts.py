"""WebSocket endpoint for TTS generation progress.

Connect: ws://host/ws/tts/{job_id}

Messages received:
    { "progress": <0–100> }

The job_id is returned by POST /api/v1/tts/generate.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.tts_progress_hub import tts_progress_hub

router = APIRouter()


@router.websocket("/ws/tts/{job_id}")
async def tts_progress_ws(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    await tts_progress_hub.register(job_id, websocket)
    # Send initial state
    await websocket.send_json({"progress": 0})
    try:
        while True:
            # Keep connection alive; all data is pushed from the hub
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await tts_progress_hub.unregister(job_id, websocket)
