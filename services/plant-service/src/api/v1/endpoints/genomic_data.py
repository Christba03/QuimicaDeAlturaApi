from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.genomic_data import (
    GenomicDataCreate,
    GenomicDataListResponse,
    GenomicDataResponse,
    GenomicDataUpdate,
)
from src.services.genomic_data_service import GenomicDataService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> GenomicDataService:
    return GenomicDataService(session=db)


@router.get("/", response_model=GenomicDataListResponse)
async def list_genomic_data(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    species: str | None = Query(None, description="Filter by species"),
    status: str | None = Query(None, description="Filter by status"),
    service: GenomicDataService = Depends(_get_service),
):
    return await service.list_genomic_data(
        page=page,
        size=size,
        species=species,
        status=status,
    )


@router.get("/{item_id}", response_model=GenomicDataResponse)
async def get_genomic_data(
    item_id: UUID,
    service: GenomicDataService = Depends(_get_service),
):
    item = await service.get_genomic_data(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Genomic data record not found")
    return item


@router.post("/", response_model=GenomicDataResponse, status_code=201)
async def create_genomic_data(
    data: GenomicDataCreate,
    service: GenomicDataService = Depends(_get_service),
):
    return await service.create_genomic_data(data)


@router.put("/{item_id}", response_model=GenomicDataResponse)
async def update_genomic_data(
    item_id: UUID,
    data: GenomicDataUpdate,
    service: GenomicDataService = Depends(_get_service),
):
    item = await service.update_genomic_data(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Genomic data record not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_genomic_data(
    item_id: UUID,
    service: GenomicDataService = Depends(_get_service),
):
    deleted = await service.delete_genomic_data(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Genomic data record not found")
