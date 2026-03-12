from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.drug_reference import (
    DrugReferenceCreate,
    DrugReferenceListResponse,
    DrugReferenceResponse,
    DrugReferenceUpdate,
)
from src.services.drug_reference_service import DrugReferenceService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> DrugReferenceService:
    return DrugReferenceService(session=db)


@router.get("/", response_model=DrugReferenceListResponse)
async def list_drug_references(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search term"),
    service: DrugReferenceService = Depends(_get_service),
):
    return await service.list_drug_references(
        page=page,
        size=size,
        search=search,
    )


@router.get("/{item_id}", response_model=DrugReferenceResponse)
async def get_drug_reference(
    item_id: UUID,
    service: DrugReferenceService = Depends(_get_service),
):
    item = await service.get_drug_reference(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Drug reference not found")
    return item


@router.post("/", response_model=DrugReferenceResponse, status_code=201)
async def create_drug_reference(
    data: DrugReferenceCreate,
    service: DrugReferenceService = Depends(_get_service),
):
    return await service.create_drug_reference(data)


@router.put("/{item_id}", response_model=DrugReferenceResponse)
async def update_drug_reference(
    item_id: UUID,
    data: DrugReferenceUpdate,
    service: DrugReferenceService = Depends(_get_service),
):
    item = await service.update_drug_reference(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Drug reference not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_drug_reference(
    item_id: UUID,
    service: DrugReferenceService = Depends(_get_service),
):
    deleted = await service.delete_drug_reference(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Drug reference not found")
