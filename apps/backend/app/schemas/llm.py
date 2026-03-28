from pydantic import BaseModel, Field


class LLMLoadRequest(BaseModel):
    model_id: int = Field(ge=1)


class LLMLoadAdapterRequest(BaseModel):
    adapter_id: int = Field(ge=1)


class LLMGenerateRequest(BaseModel):
    model_id: int = Field(ge=1)
    prompt: str = Field(min_length=1, max_length=32000)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    plugin_id: int | None = None


class LLMWebSocketStart(BaseModel):
    model_id: int = Field(ge=1)
    prompt: str = Field(min_length=1, max_length=32000)
    max_tokens: int = Field(default=256, ge=1, le=4096)
    plugin_id: int | None = None


class LLMGenerateResponse(BaseModel):
    text: str


class LLMStatusResponse(BaseModel):
    loaded_model_id: int | None
    backend: str
    device: str
    cuda_available: bool
    queue_depth: int
    busy: bool
    memory: dict[str, float]


class HardwareCheckResponse(BaseModel):
    ok: bool
    warning: str | None
    free_ram_gb: float
    free_vram_gb: float
    model_size_gb: float
