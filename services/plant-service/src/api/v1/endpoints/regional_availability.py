from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.regional_availability import (
    RegionalAvailabilityCreate,
    RegionalAvailabilityListResponse,
    RegionalAvailabilityResponse,
    RegionalAvailabilityUpdate,
)
from src.services.regional_availability_service import RegionalAvailabilityService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> RegionalAvailabilityService:
    return RegionalAvailabilityService(session=db)


@router.get("/", response_model=RegionalAvailabilityListResponse)
async def list_regional_availability(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    state: str | None = Query(None, description="Filter by state"),
    region: str | None = Query(None, description="Filter by region"),
    abundance: str | None = Query(None, description="Filter by abundance level"),
    service: RegionalAvailabilityService = Depends(_get_service),
):
    return await service.list_regional_availability(
        page=page,
        size=size,
        state=state,
        region=region,
        abundance=abundance,
    )


@router.get("/{item_id}", response_model=RegionalAvailabilityResponse)
async def get_regional_availability(
    item_id: UUID,
    service: RegionalAvailabilityService = Depends(_get_service),
):
    item = await service.get_regional_availability(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Regional availability record not found")
    return item


@router.post("/", response_model=RegionalAvailabilityResponse, status_code=201)
async def create_regional_availability(
    data: RegionalAvailabilityCreate,
    service: RegionalAvailabilityService = Depends(_get_service),
):
    return await service.create_regional_availability(data)


@router.put("/{item_id}", response_model=RegionalAvailabilityResponse)
async def update_regional_availability(
    item_id: UUID,
    data: RegionalAvailabilityUpdate,
    service: RegionalAvailabilityService = Depends(_get_service),
):
    item = await service.update_regional_availability(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Regional availability record not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_regional_availability(
    item_id: UUID,
    service: RegionalAvailabilityService = Depends(_get_service),
):
    deleted = await service.delete_regional_availability(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Regional availability record not found")
