from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.history_catalog import HistoryCatalogService
from app.services import model_service as model_service_module
from app.services.llm_service import LLMService, get_llm_service as get_llm_service_singleton
from app.services.model_service import ModelService
from app.services.adapter_service import AdapterService, get_adapter_service as get_adapter_service_singleton
from app.services.dataset_service import DatasetService, get_dataset_service as get_dataset_service_singleton
from app.services.finetune_service import FinetuneService, get_finetune_service as get_finetune_service_singleton
from app.services.plugin_service import PluginService, get_plugin_service as get_plugin_service_singleton
from app.services.system_service import SystemService
from app.services.tts_service import TTSService, get_tts_service as get_tts_service_singleton
from app.services.voice_service import VoiceService, get_voice_service as get_voice_service_singleton


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_system_service() -> SystemService:
    return SystemService()


def get_model_service() -> ModelService:
    return model_service_module.get_model_service()


def get_llm_service() -> LLMService:
    return get_llm_service_singleton()


def get_plugin_service() -> PluginService:
    return get_plugin_service_singleton()


def get_dataset_service() -> DatasetService:
    return get_dataset_service_singleton()


def get_finetune_service() -> FinetuneService:
    return get_finetune_service_singleton()


def get_adapter_service() -> AdapterService:
    return get_adapter_service_singleton()


def get_history_catalog_service() -> HistoryCatalogService:
    return HistoryCatalogService()


def get_tts_service() -> TTSService:
    return get_tts_service_singleton()


def get_voice_service() -> VoiceService:
    return get_voice_service_singleton()
