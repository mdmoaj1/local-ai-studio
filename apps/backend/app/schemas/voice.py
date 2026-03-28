"""Pydantic schemas for Voice endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VoiceOut(BaseModel):
    id: int
    name: str
    path: str
    duration: float = Field(0.0, description="Audio duration in seconds")
    created_at: datetime

    model_config = {"from_attributes": True}


class VoiceDeleteRequest(BaseModel):
    id: int
