from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.inference_job import (
    InferenceJobCreate,
    InferenceJobListResponse,
    InferenceJobResponse,
    InferenceJobUpdate,
)
from src.services.inference_job_service import InferenceJobService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> InferenceJobService:
    return InferenceJobService(session=db)


@router.get("/", response_model=InferenceJobListResponse)
async def list_inference_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by job status"),
    flagged: bool | None = Query(None, description="Filter by flagged state"),
    service: InferenceJobService = Depends(_get_service),
):
    return await service.list_inference_jobs(
        page=page,
        size=size,
        status=status,
        flagged=flagged,
    )


@router.get("/{item_id}", response_model=InferenceJobResponse)
async def get_inference_job(
    item_id: UUID,
    service: InferenceJobService = Depends(_get_service),
):
    item = await service.get_inference_job(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inference job not found")
    return item


@router.post("/", response_model=InferenceJobResponse, status_code=201)
async def create_inference_job(
    data: InferenceJobCreate,
    service: InferenceJobService = Depends(_get_service),
):
    return await service.create_inference_job(data)


@router.put("/{item_id}", response_model=InferenceJobResponse)
async def update_inference_job(
    item_id: UUID,
    data: InferenceJobUpdate,
    service: InferenceJobService = Depends(_get_service),
):
    item = await service.update_inference_job(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Inference job not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_inference_job(
    item_id: UUID,
    service: InferenceJobService = Depends(_get_service),
):
    deleted = await service.delete_inference_job(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inference job not found")
