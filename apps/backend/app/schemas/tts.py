"""Pydantic schemas for TTS endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TTSGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096, description="Text to synthesise")
    voice_id: int = Field(..., description="ID of the speaker voice to clone")
    model_id: int = Field(..., description="ID of the TTS model to use")


class TTSGenerateResponse(BaseModel):
    audio_url: str = Field(..., description="URL to the generated audio file")
    duration: float = Field(..., description="Duration of the generated audio in seconds")
    history_id: int = Field(..., description="ID of the TTS history record")
    job_id: str = Field(..., description="Job identifier for WebSocket progress tracking")

    model_config = {"from_attributes": True}


class TTSHistoryOut(BaseModel):
    id: int
    text: str
    voice_id: int | None
    model_id: int | None
    audio_path: str
    created_at: datetime

    model_config = {"from_attributes": True}
