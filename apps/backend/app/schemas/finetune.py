from datetime import datetime

from pydantic import BaseModel, Field


class DatasetOut(BaseModel):
    id: int
    name: str
    path: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IdPayload(BaseModel):
    id: int = Field(ge=1)


class FinetuneStartRequest(BaseModel):
    model_id: int = Field(ge=1)
    dataset_id: int = Field(ge=1)
    adapter_name: str = Field(min_length=1, max_length=256)
    epochs: int = Field(default=1, ge=1, le=100)
    learning_rate: float = Field(default=2e-4, gt=0, le=1.0)


class JobOut(BaseModel):
    id: int
    type: str
    status: str
    progress: float
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdapterOut(BaseModel):
    id: int
    name: str
    path: str
    base_model: str
    size: int
    created_at: datetime

    model_config = {"from_attributes": True}
