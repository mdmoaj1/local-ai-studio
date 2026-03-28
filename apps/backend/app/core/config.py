from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_mode: str = "web"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "sqlite+aiosqlite:///./local_ai_studio.db"
    system_ws_interval_seconds: float = 1.0
    models_root: str = ""
    datasets_root: str = ""
    hf_token: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def resolve_models_root(self) -> Path:
        if self.models_root.strip():
            return Path(self.models_root).expanduser().resolve()
        # Monorepo default: <repo>/models (this file: app/core/config.py -> parents[2] == apps/backend)
        backend_dir = Path(__file__).resolve().parents[2]
        repo_root = backend_dir.parents[1]
        return (repo_root / "models").resolve()

    def resolve_datasets_root(self) -> Path:
        if self.datasets_root.strip():
            return Path(self.datasets_root).expanduser().resolve()
        backend_dir = Path(__file__).resolve().parents[2]
        repo_root = backend_dir.parents[1]
        return (repo_root / "datasets").resolve()

    def resolve_adapters_root(self) -> Path:
        return (self.resolve_models_root() / "adapters").resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
