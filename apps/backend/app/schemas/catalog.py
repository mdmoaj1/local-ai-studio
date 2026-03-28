from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: int | None
    prompt: str
    response: str
    created_at: datetime


class HistoryEntryCreate(BaseModel):
    model_id: int | None = None
    prompt: str = ""
    response: str = ""
