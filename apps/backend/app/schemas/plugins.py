from pydantic import BaseModel, Field


class PluginManifestJson(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    title: str = ""
    description: str = ""


class PluginOut(BaseModel):
    id: int
    name: str
    title: str
    description: str
    enabled: bool
    path: str


class PluginEnabledPatch(BaseModel):
    enabled: bool
