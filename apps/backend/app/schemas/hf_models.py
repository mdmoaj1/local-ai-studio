from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


ModelKindLiteral = Literal["llm", "tts", "voice", "gguf"]
RuntimeLiteral = Literal["transformers", "gguf", "unknown"]


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ModelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    hf_repo_id: str = Field(min_length=1, max_length=512)
    type: ModelKindLiteral = "llm"
    runtime: str = "transformers"
    revision: str | None = Field(default=None, max_length=128)


class ModelIdRequest(BaseModel):
    model_id: int = Field(ge=1)


class ModelDownloadRequest(BaseModel):
    model_id: int = Field(ge=1)
    revision: str | None = Field(default=None, max_length=128)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ModelOut(BaseModel):
    """Installed (DB-backed) model response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    hf_repo_id: str
    local_path: str
    size: int
    status: str
    runtime: str = "transformers"
    model_type: str = Field(exclude=True)
    created_at: datetime

    @computed_field
    @property
    def type(self) -> str:  # noqa: A003
        return self.model_type


class RegistryModelOut(BaseModel):
    """A model entry from registry.json (no DB row required)."""
    name: str
    hf_repo: str
    type: str
    runtime: str
    description: str = ""


class MergedModelOut(BaseModel):
    """Union of registry metadata + optional install state.

    When present in the DB the ``id`` / ``status`` / ``size`` / ``local_path``
    fields are populated; registry-only entries carry ``None`` / defaults.
    """
    # Registry fields (always present)
    name: str
    hf_repo: str
    type: str
    runtime: str
    description: str = ""

    # DB fields (populated when the model has been added / installed)
    id: int | None = None
    status: str = "not_installed"
    size: int = 0
    local_path: str = ""


# ---------------------------------------------------------------------------
# WebSocket progress payload
# ---------------------------------------------------------------------------

class DownloadProgressPayload(BaseModel):
    progress: float
    speed: float
    downloaded: float
    total: float
    status: str
