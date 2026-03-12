from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.ethnobotanical import (
    EthnobotanicalCreate,
    EthnobotanicalListResponse,
    EthnobotanicalResponse,
    EthnobotanicalUpdate,
)
from src.services.ethnobotanical_service import EthnobotanicalService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> EthnobotanicalService:
    return EthnobotanicalService(session=db)


@router.get("/", response_model=EthnobotanicalListResponse)
async def list_ethnobotanical(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search term"),
    evidence_level: str | None = Query(None, description="Filter by evidence level"),
    region: str | None = Query(None, description="Filter by region"),
    service: EthnobotanicalService = Depends(_get_service),
):
    return await service.list_ethnobotanical(
        page=page,
        size=size,
        search=search,
        evidence_level=evidence_level,
        region=region,
    )


@router.get("/{item_id}", response_model=EthnobotanicalResponse)
async def get_ethnobotanical(
    item_id: UUID,
    service: EthnobotanicalService = Depends(_get_service),
):
    item = await service.get_ethnobotanical(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ethnobotanical record not found")
    return item


@router.post("/", response_model=EthnobotanicalResponse, status_code=201)
async def create_ethnobotanical(
    data: EthnobotanicalCreate,
    service: EthnobotanicalService = Depends(_get_service),
):
    return await service.create_ethnobotanical(data)


@router.put("/{item_id}", response_model=EthnobotanicalResponse)
async def update_ethnobotanical(
    item_id: UUID,
    data: EthnobotanicalUpdate,
    service: EthnobotanicalService = Depends(_get_service),
):
    item = await service.update_ethnobotanical(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Ethnobotanical record not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_ethnobotanical(
    item_id: UUID,
    service: EthnobotanicalService = Depends(_get_service),
):
    deleted = await service.delete_ethnobotanical(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ethnobotanical record not found")
