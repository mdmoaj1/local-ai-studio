import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.ws_manager import download_progress, ws_manager

router = APIRouter()

@router.websocket("/ws/download/{model_id}")
async def download_progress_ws(websocket: WebSocket, model_id: int) -> None:
    await ws_manager.connect(websocket, model_id)
    
    async def send_updates() -> None:
        try:
            while True:
                progress = download_progress.get(model_id)
                if progress:
                    await ws_manager.send(websocket, progress)
                await asyncio.sleep(0.5)
        except Exception:
            pass

    sender_task = asyncio.create_task(send_updates())
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        sender_task.cancel()
        ws_manager.disconnect(websocket, model_id)
