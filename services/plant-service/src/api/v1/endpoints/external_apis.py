from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.external_api import (
    ExternalApiCreate,
    ExternalApiListResponse,
    ExternalApiResponse,
    ExternalApiUpdate,
)
from src.services.external_api_service import ExternalApiService

router = APIRouter()


async def _get_service(db: AsyncSession = Depends(get_db)) -> ExternalApiService:
    return ExternalApiService(session=db)


@router.get("/", response_model=ExternalApiListResponse)
async def list_external_apis(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
    service: ExternalApiService = Depends(_get_service),
):
    return await service.list_apis(page=page, size=size, search=search, is_active=is_active)


@router.get("/{item_id}", response_model=ExternalApiResponse)
async def get_external_api(
    item_id: UUID,
    service: ExternalApiService = Depends(_get_service),
):
    item = await service.get_api(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="External API not found")
    return item


@router.post("/", response_model=ExternalApiResponse, status_code=201)
async def create_external_api(
    data: ExternalApiCreate,
    service: ExternalApiService = Depends(_get_service),
):
    return await service.create_api(data)


@router.put("/{item_id}", response_model=ExternalApiResponse)
async def update_external_api(
    item_id: UUID,
    data: ExternalApiUpdate,
    service: ExternalApiService = Depends(_get_service),
):
    item = await service.update_api(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="External API not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_external_api(
    item_id: UUID,
    service: ExternalApiService = Depends(_get_service),
):
    deleted = await service.delete_api(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="External API not found")
