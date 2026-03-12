from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel


class OntologyTermBase(BaseModel):
    canonical_term: str
    icd10_code: Optional[str] = None
    mesh_id: Optional[str] = None
    synonyms: Optional[list[Any]] = None
    category: Optional[str] = None
    description: Optional[str] = None


class OntologyTermCreate(OntologyTermBase):
    pass


class OntologyTermUpdate(BaseModel):
    canonical_term: Optional[str] = None
    icd10_code: Optional[str] = None
    mesh_id: Optional[str] = None
    synonyms: Optional[list[Any]] = None
    category: Optional[str] = None
    description: Optional[str] = None


class OntologyTermResponse(OntologyTermBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OntologyTermListResponse(BaseModel):
    items: list[OntologyTermResponse]
    total: int
    page: int
    size: int
    pages: int
