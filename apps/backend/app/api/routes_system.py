from fastapi import APIRouter, Depends

from app.api.deps import get_system_service
from app.services.system_service import SystemService

router = APIRouter()


@router.get("/metrics")
async def get_system_metrics(svc: SystemService = Depends(get_system_service)) -> dict[str, float | int]:
    return svc.snapshot().as_ws_payload()
