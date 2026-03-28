from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_adapter_service, get_dataset_service, get_db, get_finetune_service
from app.schemas.finetune import AdapterOut, DatasetOut, FinetuneStartRequest, IdPayload, JobOut
from app.services.adapter_service import AdapterService
from app.services.dataset_service import DatasetService
from app.services.finetune_service import FinetuneService

router = APIRouter()


@router.get("/datasets", response_model=list[DatasetOut])
async def list_datasets(
    session: AsyncSession = Depends(get_db),
    svc: DatasetService = Depends(get_dataset_service),
) -> list[DatasetOut]:
    rows = await svc.list_datasets(session)
    return [DatasetOut.model_validate(r) for r in rows]


@router.post("/datasets/add", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def add_dataset(
    session: AsyncSession = Depends(get_db),
    svc: DatasetService = Depends(get_dataset_service),
    file: UploadFile = File(...),
    name: str | None = Form(None),
) -> DatasetOut:
    try:
        row = await svc.add_from_upload(session, file=file, display_name=name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return DatasetOut.model_validate(row)


@router.post("/datasets/delete")
async def delete_dataset(
    body: IdPayload,
    session: AsyncSession = Depends(get_db),
    svc: DatasetService = Depends(get_dataset_service),
) -> dict[str, bool]:
    try:
        await svc.delete(session, body.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/finetune/start", response_model=JobOut)
async def finetune_start(
    body: FinetuneStartRequest,
    session: AsyncSession = Depends(get_db),
    svc: FinetuneService = Depends(get_finetune_service),
) -> JobOut:
    try:
        job = await svc.start_lora(
            session,
            model_id=body.model_id,
            dataset_id=body.dataset_id,
            adapter_name=body.adapter_name,
            epochs=body.epochs,
            learning_rate=body.learning_rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JobOut.model_validate(job)


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    svc: FinetuneService = Depends(get_finetune_service),
) -> JobOut:
    row = await svc.get_job(session, job_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobOut.model_validate(row)


@router.get("/adapters", response_model=list[AdapterOut])
async def list_adapters(
    session: AsyncSession = Depends(get_db),
    svc: AdapterService = Depends(get_adapter_service),
) -> list[AdapterOut]:
    rows = await svc.list_adapters(session)
    return [AdapterOut.model_validate(r) for r in rows]


@router.post("/adapters/delete")
async def delete_adapter(
    body: IdPayload,
    session: AsyncSession = Depends(get_db),
    svc: AdapterService = Depends(get_adapter_service),
) -> dict[str, bool]:
    try:
        await svc.delete(session, body.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}
