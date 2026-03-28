from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.train_progress_hub import train_progress_hub
from app.db.models import JobRecord
from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.websocket("/ws/train/{job_id}")
async def train_progress_ws(websocket: WebSocket, job_id: int) -> None:
    await websocket.accept()
    hub = train_progress_hub
    await hub.register(job_id, websocket)
    async with AsyncSessionLocal() as session:
        row = await session.get(JobRecord, job_id)
    if row is not None:
        await websocket.send_json(
            {
                "snapshot": True,
                "status": row.status,
                "progress": row.progress,
                "message": row.message,
            },
        )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.unregister(job_id, websocket)
