from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_llm_service
from app.services.llm_service import LLMService
from app.services.llm_stream_session import handle_llm_websocket

router = APIRouter()


@router.websocket("/ws/generate")
async def llm_generate_ws(
    websocket: WebSocket,
    llm_service: LLMService = Depends(get_llm_service),
) -> None:
    await websocket.accept()
    try:
        await handle_llm_websocket(websocket, llm_service)
    except WebSocketDisconnect:
        return
