"""Voice library API routes.

GET  /api/v1/voices          — list all registered voices
POST /api/v1/voices/upload   — upload a new voice (multipart)
POST /api/v1/voices/delete   — delete a voice by id
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_voice_service
from app.schemas.voice import VoiceDeleteRequest, VoiceOut
from app.services.voice_service import VoiceService

router = APIRouter()


@router.get("", response_model=list[VoiceOut])
async def list_voices(
    session: AsyncSession = Depends(get_db),
    svc: VoiceService = Depends(get_voice_service),
) -> list[VoiceOut]:
    rows = await svc.list_voices(session)
    result: list[VoiceOut] = []
    for r in rows:
        duration = svc.get_duration_for(r)
        result.append(
            VoiceOut(
                id=r.id,
                name=r.name,
                path=r.path,
                duration=duration,
                created_at=r.created_at,
            )
        )
    return result


@router.post("/upload", response_model=VoiceOut, status_code=status.HTTP_201_CREATED)
async def upload_voice(
    name: str = Form(..., description="Unique display name for the voice"),
    file: UploadFile = File(..., description="WAV or MP3 reference audio"),
    session: AsyncSession = Depends(get_db),
    svc: VoiceService = Depends(get_voice_service),
) -> VoiceOut:
    try:
        row = await svc.upload_voice(session, name=name, file=file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    duration = svc.get_duration_for(row)
    return VoiceOut(
        id=row.id,
        name=row.name,
        path=row.path,
        duration=duration,
        created_at=row.created_at,
    )


@router.post("/delete")
async def delete_voice(
    body: VoiceDeleteRequest,
    session: AsyncSession = Depends(get_db),
    svc: VoiceService = Depends(get_voice_service),
) -> dict[str, bool]:
    try:
        await svc.delete_voice(session, body.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"ok": True}
