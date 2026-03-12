from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.data_pipeline import (
    DataPipelineCreate,
    DataPipelineListResponse,
    DataPipelineResponse,
    DataPipelineUpdate,
)
from src.services.data_pipeline_service import DataPipelineService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> DataPipelineService:
    return DataPipelineService(session=db)


@router.get("/", response_model=DataPipelineListResponse)
async def list_data_pipelines(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by pipeline status"),
    service: DataPipelineService = Depends(_get_service),
):
    return await service.list_pipelines(page=page, size=size, status=status)


@router.get("/{item_id}", response_model=DataPipelineResponse)
async def get_data_pipeline(
    item_id: UUID,
    service: DataPipelineService = Depends(_get_service),
):
    item = await service.get_pipeline(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return item


@router.post("/", response_model=DataPipelineResponse, status_code=201)
async def create_data_pipeline(
    data: DataPipelineCreate,
    service: DataPipelineService = Depends(_get_service),
):
    return await service.create_pipeline(data)


@router.put("/{item_id}", response_model=DataPipelineResponse)
async def update_data_pipeline(
    item_id: UUID,
    data: DataPipelineUpdate,
    service: DataPipelineService = Depends(_get_service),
):
    item = await service.update_pipeline(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_data_pipeline(
    item_id: UUID,
    service: DataPipelineService = Depends(_get_service),
):
    deleted = await service.delete_pipeline(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")


@router.post("/{item_id}/trigger", response_model=DataPipelineResponse)
async def trigger_pipeline(item_id: UUID, service: DataPipelineService = Depends(_get_service)):
    pipeline = await service.trigger_pipeline(item_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline
