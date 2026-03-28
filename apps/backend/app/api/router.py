from fastapi import APIRouter

from app.api import routes_finetune
from app.api import routes_models
from app.api import routes_plugins
from app.api import routes_system
from app.api import routes_tts
from app.api import routes_voices
from app.api.v1 import history as history_v1
from app.api.v1 import llm as llm_v1

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(routes_system.router, prefix="/system", tags=["system"])
api_router.include_router(routes_models.router, prefix="/models", tags=["models"])
api_router.include_router(llm_v1.router, prefix="/llm", tags=["llm"])
api_router.include_router(routes_plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(history_v1.router, prefix="/history", tags=["history"])
api_router.include_router(routes_finetune.router, tags=["finetune"])
api_router.include_router(routes_tts.router, prefix="/tts", tags=["tts"])
api_router.include_router(routes_voices.router, prefix="/voices", tags=["voices"])
