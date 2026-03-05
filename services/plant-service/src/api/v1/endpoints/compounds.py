from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.compound import (
    CompoundCreate,
    CompoundListResponse,
    CompoundResponse,
    CompoundUpdate,
    PlantCompoundCreate,
    PlantCompoundResponse,
)
from src.services.compound_service import CompoundService

router = APIRouter()


async def _get_compound_service(
    db: AsyncSession = Depends(get_db),
) -> CompoundService:
    return CompoundService(session=db)


@router.get("/", response_model=CompoundListResponse)
async def list_compounds(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by name"),
    compound_class: str | None = Query(None, description="Filter by compound class"),
    service: CompoundService = Depends(_get_compound_service),
):
    return await service.list_compounds(
        page=page, size=size, search=search, compound_class=compound_class
    )


@router.get("/{compound_id}", response_model=CompoundResponse)
async def get_compound(
    compound_id: UUID,
    service: CompoundService = Depends(_get_compound_service),
):
    compound = await service.get_compound(compound_id)
    if not compound:
        raise HTTPException(status_code=404, detail="Compound not found")
    return compound


@router.post("/", response_model=CompoundResponse, status_code=201)
async def create_compound(
    data: CompoundCreate,
    service: CompoundService = Depends(_get_compound_service),
):
    return await service.create_compound(data)


@router.put("/{compound_id}", response_model=CompoundResponse)
async def update_compound(
    compound_id: UUID,
    data: CompoundUpdate,
    service: CompoundService = Depends(_get_compound_service),
):
    compound = await service.update_compound(compound_id, data)
    if not compound:
        raise HTTPException(status_code=404, detail="Compound not found")
    return compound


@router.delete("/{compound_id}", status_code=204)
async def delete_compound(
    compound_id: UUID,
    service: CompoundService = Depends(_get_compound_service),
):
    deleted = await service.delete_compound(compound_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Compound not found")


@router.post("/link", response_model=PlantCompoundResponse, status_code=201)
async def link_compound_to_plant(
    data: PlantCompoundCreate,
    service: CompoundService = Depends(_get_compound_service),
):
    return await service.link_compound_to_plant(data)


@router.delete("/link/{plant_id}/{compound_id}", status_code=204)
async def unlink_compound_from_plant(
    plant_id: UUID,
    compound_id: UUID,
    service: CompoundService = Depends(_get_compound_service),
):
    await service.unlink_compound_from_plant(plant_id, compound_id)


@router.get("/plant/{plant_id}", response_model=list[PlantCompoundResponse])
async def get_plant_compounds(
    plant_id: UUID,
    service: CompoundService = Depends(_get_compound_service),
):
    return await service.get_plant_compounds(plant_id)
