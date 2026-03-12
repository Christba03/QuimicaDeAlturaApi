from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.ontology_term import (
    OntologyTermCreate,
    OntologyTermListResponse,
    OntologyTermResponse,
    OntologyTermUpdate,
)
from src.services.ontology_term_service import OntologyTermService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> OntologyTermService:
    return OntologyTermService(session=db)


@router.get("/", response_model=OntologyTermListResponse)
async def list_ontology_terms(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search term"),
    service: OntologyTermService = Depends(_get_service),
):
    return await service.list_ontology_terms(
        page=page,
        size=size,
        search=search,
    )


@router.get("/{item_id}", response_model=OntologyTermResponse)
async def get_ontology_term(
    item_id: UUID,
    service: OntologyTermService = Depends(_get_service),
):
    item = await service.get_ontology_term(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ontology term not found")
    return item


@router.post("/", response_model=OntologyTermResponse, status_code=201)
async def create_ontology_term(
    data: OntologyTermCreate,
    service: OntologyTermService = Depends(_get_service),
):
    return await service.create_ontology_term(data)


@router.put("/{item_id}", response_model=OntologyTermResponse)
async def update_ontology_term(
    item_id: UUID,
    data: OntologyTermUpdate,
    service: OntologyTermService = Depends(_get_service),
):
    item = await service.update_ontology_term(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Ontology term not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_ontology_term(
    item_id: UUID,
    service: OntologyTermService = Depends(_get_service),
):
    deleted = await service.delete_ontology_term(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ontology term not found")
