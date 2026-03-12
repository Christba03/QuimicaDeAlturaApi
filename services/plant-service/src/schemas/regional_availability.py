from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from src.models.regional_availability import AbundanceLevel


class RegionalAvailabilityBase(BaseModel):
    species: str
    state: Optional[str] = None
    region: Optional[str] = None
    source: Optional[str] = None
    abundance: Optional[AbundanceLevel] = None
    last_updated: Optional[datetime] = None
    notes: Optional[str] = None


class RegionalAvailabilityCreate(RegionalAvailabilityBase):
    pass


class RegionalAvailabilityUpdate(BaseModel):
    species: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    source: Optional[str] = None
    abundance: Optional[AbundanceLevel] = None
    last_updated: Optional[datetime] = None
    notes: Optional[str] = None


class RegionalAvailabilityResponse(RegionalAvailabilityBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RegionalAvailabilityListResponse(BaseModel):
    items: list[RegionalAvailabilityResponse]
    total: int
    page: int
    size: int
    pages: int
