"""TTS API routes.

POST /api/v1/tts/generate  — synthesise speech
GET  /api/v1/tts/history   — recent generation history
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_tts_service
from app.schemas.tts import TTSGenerateRequest, TTSGenerateResponse, TTSHistoryOut
from app.services.tts_service import TTSService

router = APIRouter()


@router.post("/generate", response_model=TTSGenerateResponse, status_code=status.HTTP_200_OK)
async def tts_generate(
    body: TTSGenerateRequest,
    session: AsyncSession = Depends(get_db),
    svc: TTSService = Depends(get_tts_service),
) -> TTSGenerateResponse:
    """Synthesise speech from *text* using the selected voice and model.

    Connect to ``/ws/tts/{job_id}`` (returned in the response) to receive
    real-time progress events during generation.
    """
    try:
        audio_url, duration, history_id, job_id = await svc.generate(
            text=body.text,
            voice_id=body.voice_id,
            model_id=body.model_id,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return TTSGenerateResponse(
        audio_url=audio_url,
        duration=duration,
        history_id=history_id,
        job_id=job_id,
    )


@router.get("/history", response_model=list[TTSHistoryOut])
async def tts_history(
    session: AsyncSession = Depends(get_db),
    svc: TTSService = Depends(get_tts_service),
) -> list[TTSHistoryOut]:
    rows = await svc.list_history(session)
    return [TTSHistoryOut.model_validate(r) for r in rows]
