from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.model_version import (
    ModelVersionActivateResponse,
    ModelVersionCreate,
    ModelVersionListResponse,
    ModelVersionResponse,
    ModelVersionUpdate,
)
from src.services.model_version_service import ModelVersionService

router = APIRouter()


async def _get_service(db: AsyncSession = Depends(get_db)) -> ModelVersionService:
    return ModelVersionService(session=db)


@router.get("/", response_model=ModelVersionListResponse)
async def list_model_versions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    service: ModelVersionService = Depends(_get_service),
):
    return await service.list_versions(page=page, size=size, status=status)


@router.get("/{item_id}", response_model=ModelVersionResponse)
async def get_model_version(
    item_id: UUID,
    service: ModelVersionService = Depends(_get_service),
):
    item = await service.get_version(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Model version not found")
    return item


@router.post("/", response_model=ModelVersionResponse, status_code=201)
async def create_model_version(
    data: ModelVersionCreate,
    service: ModelVersionService = Depends(_get_service),
):
    return await service.create_version(data)


@router.put("/{item_id}", response_model=ModelVersionResponse)
async def update_model_version(
    item_id: UUID,
    data: ModelVersionUpdate,
    service: ModelVersionService = Depends(_get_service),
):
    item = await service.update_version(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Model version not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_model_version(
    item_id: UUID,
    service: ModelVersionService = Depends(_get_service),
):
    deleted = await service.delete_version(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model version not found")


@router.put("/{item_id}/activate", response_model=ModelVersionActivateResponse)
async def activate_model_version(
    item_id: UUID,
    service: ModelVersionService = Depends(_get_service),
):
    version = await service.activate_version(item_id)
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")
    return ModelVersionActivateResponse(
        id=version.id, status=version.status, message="Model version activated"
    )


@router.put("/{item_id}/rollback", response_model=ModelVersionActivateResponse)
async def rollback_model_version(
    item_id: UUID,
    service: ModelVersionService = Depends(_get_service),
):
    version = await service.rollback_version(item_id)
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")
    return ModelVersionActivateResponse(
        id=version.id, status=version.status, message="Model version rolled back"
    )
