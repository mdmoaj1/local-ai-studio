import app.engine_bootstrap  # noqa: F401, E402

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text, update

from app.api.router import api_router
from app.api.websocket import download as download_ws
from app.api.websocket import generate as generate_ws
from app.api.websocket import system as system_ws
from app.api.websocket import train as train_ws
from app.api.websocket import tts as tts_ws
from app.core.config import get_settings
from app.core.download_progress_hub import download_progress_hub
from app.core.job_manager import get_job_manager
from app.core.train_progress_hub import train_progress_hub
from app.core.tts_progress_hub import tts_progress_hub
from app.db import models as _models  # noqa: F401
from app.db.base import Base
from app.db.models import JobRecord
from app.db.session import AsyncSessionLocal, engine
from app.services.llm_service import get_llm_service
from app.services.plugin_service import get_plugin_service

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    loop = asyncio.get_running_loop()
    download_progress_hub.set_loop(loop)
    train_progress_hub.set_loop(loop)
    tts_progress_hub.set_loop(loop)
    get_job_manager().set_loop(loop)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Safe migration: add runtime column to models table for existing DBs.
        # SQLite ignores ADD COLUMN if the column already exists when using
        # IF NOT EXISTS (SQLite ≥ 3.37.0, shipped with Python 3.12).
        try:
            await conn.execute(
                text("ALTER TABLE models ADD COLUMN runtime VARCHAR(32) NOT NULL DEFAULT 'transformers'")
            )
        except Exception:
            pass  # Column already exists — safe to ignore
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(JobRecord)
            .where(JobRecord.status == "running")
            .values(status="error", message="Server restarted during training"),
        )
        await session.execute(
            update(JobRecord)
            .where(JobRecord.status == "queued")
            .values(status="error", message="Training queue was reset on server restart"),
        )
        await session.commit()
        await get_plugin_service().sync_from_disk(session)
    get_llm_service().start_scheduler()
    yield
    await get_llm_service().stop_scheduler()
    get_job_manager().shutdown()


app = FastAPI(
    title="Local AI Studio API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(system_ws.router)
app.include_router(download_ws.router)
app.include_router(generate_ws.router)
app.include_router(train_ws.router)
app.include_router(tts_ws.router)

# Static file mounts — audio outputs and voice reference files
_audio_dir = Path("outputs/audio")
_audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_audio_dir)), name="audio")

_voices_dir = Path("voices")
_voices_dir.mkdir(parents=True, exist_ok=True)
app.mount("/voices-files", StaticFiles(directory=str(_voices_dir)), name="voices-files")
