from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from src.models.ethnobotanical import EvidenceLevel


class EthnobotanicalBase(BaseModel):
    species: str
    community: Optional[str] = None
    region: Optional[str] = None
    condition_treated: Optional[str] = None
    preparation_method: Optional[str] = None
    raw_material_part: Optional[str] = None
    documenter: Optional[str] = None
    year: Optional[int] = None
    evidence_level: Optional[EvidenceLevel] = None
    notes: Optional[str] = None


class EthnobotanicalCreate(EthnobotanicalBase):
    pass


class EthnobotanicalUpdate(BaseModel):
    species: Optional[str] = None
    community: Optional[str] = None
    region: Optional[str] = None
    condition_treated: Optional[str] = None
    preparation_method: Optional[str] = None
    raw_material_part: Optional[str] = None
    documenter: Optional[str] = None
    year: Optional[int] = None
    evidence_level: Optional[EvidenceLevel] = None
    notes: Optional[str] = None


class EthnobotanicalResponse(EthnobotanicalBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EthnobotanicalListResponse(BaseModel):
    items: list[EthnobotanicalResponse]
    total: int
    page: int
    size: int
    pages: int
