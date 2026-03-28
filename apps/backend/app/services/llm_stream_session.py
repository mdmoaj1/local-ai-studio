from __future__ import annotations

from fastapi import WebSocket
from pydantic import ValidationError

from app.db.session import AsyncSessionLocal
from app.schemas.llm import LLMWebSocketStart
from app.services.llm_service import LLMService


async def handle_llm_websocket(websocket: WebSocket, llm_service: LLMService) -> None:
    raw = await websocket.receive_text()
    try:
        body = LLMWebSocketStart.model_validate_json(raw)
    except ValidationError as exc:
        await websocket.send_json({"error": "invalid_payload", "detail": exc.errors()})
        return

    async def on_token(t: str) -> None:
        await websocket.send_json({"token": t})

    async def job() -> str:
        async with AsyncSessionLocal() as session:
            return await llm_service.stream_generate(
                body.model_id,
                body.prompt,
                body.max_tokens,
                body.plugin_id,
                session,
                on_token,
            )

    try:
        await llm_service.scheduler.submit(job)
        await websocket.send_json({"done": True})
    except Exception as exc:
        await websocket.send_json({"error": str(exc)})
