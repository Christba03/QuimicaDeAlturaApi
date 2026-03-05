from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_redis
from src.core.cache import PlantCache
from src.core.events import EventPublisher
from src.models.plant import PlantStatus
from src.schemas.plant import (
    PlantCreate,
    PlantDetail,
    PlantListResponse,
    PlantResponse,
    PlantUpdate,
)
from src.services.plant_service import PlantService

router = APIRouter()


async def _get_plant_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PlantService:
    cache = PlantCache(redis) if redis else None
    events = EventPublisher(redis) if redis else None
    return PlantService(session=db, cache=cache, events=events)


@router.get("/", response_model=PlantListResponse)
async def list_plants(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name"),
    family: str | None = Query(None, description="Filter by family"),
    status: PlantStatus | None = Query(None, description="Filter by status"),
    service: PlantService = Depends(_get_plant_service),
):
    return await service.list_plants(
        page=page, size=size, search=search, family=family, status=status
    )


@router.get("/{plant_id}", response_model=PlantDetail)
async def get_plant(
    plant_id: UUID,
    service: PlantService = Depends(_get_plant_service),
):
    plant = await service.get_plant(plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.post("/", response_model=PlantResponse, status_code=201)
async def create_plant(
    data: PlantCreate,
    service: PlantService = Depends(_get_plant_service),
):
    return await service.create_plant(data)


@router.put("/{plant_id}", response_model=PlantResponse)
async def update_plant(
    plant_id: UUID,
    data: PlantUpdate,
    service: PlantService = Depends(_get_plant_service),
):
    plant = await service.update_plant(plant_id, data)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.delete("/{plant_id}", status_code=204)
async def delete_plant(
    plant_id: UUID,
    service: PlantService = Depends(_get_plant_service),
):
    deleted = await service.delete_plant(plant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plant not found")
