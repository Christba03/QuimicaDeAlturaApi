from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class DrugReferenceBase(BaseModel):
    drug_name: str
    active_ingredient: Optional[str] = None
    linked_compound: Optional[UUID] = None
    linked_plant: Optional[UUID] = None
    pathway_overlap: Optional[str] = None
    similarity_score: Optional[float] = None
    mechanism: Optional[str] = None
    notes: Optional[str] = None


class DrugReferenceCreate(DrugReferenceBase):
    pass


class DrugReferenceUpdate(BaseModel):
    drug_name: Optional[str] = None
    active_ingredient: Optional[str] = None
    linked_compound: Optional[UUID] = None
    linked_plant: Optional[UUID] = None
    pathway_overlap: Optional[str] = None
    similarity_score: Optional[float] = None
    mechanism: Optional[str] = None
    notes: Optional[str] = None


class DrugReferenceResponse(DrugReferenceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DrugReferenceListResponse(BaseModel):
    items: list[DrugReferenceResponse]
    total: int
    page: int
    size: int
    pages: int
