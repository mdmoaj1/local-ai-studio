from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_llm_service
from app.schemas.llm import (
    HardwareCheckResponse,
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMLoadAdapterRequest,
    LLMLoadRequest,
    LLMStatusResponse,
)
from app.services.llm_service import LLMService

router = APIRouter()


@router.post("/load")
async def llm_load(
    body: LLMLoadRequest,
    session: AsyncSession = Depends(get_db),
    svc: LLMService = Depends(get_llm_service),
) -> dict[str, bool]:
    try:
        await svc.load(session, body.model_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/unload")
async def llm_unload(svc: LLMService = Depends(get_llm_service)) -> dict[str, bool]:
    await svc.unload()
    return {"ok": True}


@router.post("/load_adapter")
async def llm_load_adapter(
    body: LLMLoadAdapterRequest,
    session: AsyncSession = Depends(get_db),
    svc: LLMService = Depends(get_llm_service),
) -> dict[str, bool]:
    try:
        await svc.load_adapter(session, body.adapter_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/generate", response_model=LLMGenerateResponse)
async def llm_generate(
    body: LLMGenerateRequest,
    session: AsyncSession = Depends(get_db),
    svc: LLMService = Depends(get_llm_service),
) -> LLMGenerateResponse:
    try:
        text = await svc.generate(
            body.model_id,
            body.prompt,
            body.max_tokens,
            body.plugin_id,
            session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return LLMGenerateResponse(text=text)


@router.get("/status", response_model=LLMStatusResponse)
def llm_status(svc: LLMService = Depends(get_llm_service)) -> LLMStatusResponse:
    return svc.status()


@router.get("/hardware-check/{model_id}", response_model=HardwareCheckResponse)
async def llm_hardware_check(
    model_id: int,
    session: AsyncSession = Depends(get_db),
    svc: LLMService = Depends(get_llm_service),
) -> HardwareCheckResponse:
    return await svc.hardware_check(model_id, session)
