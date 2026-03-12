from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.plant import PlantStatus


class PlantBase(BaseModel):
    scientific_name: str = Field(..., max_length=255)
    common_name: str | None = Field(None, max_length=255)
    family: str | None = Field(None, max_length=128)
    genus: str | None = Field(None, max_length=128)
    species: str | None = Field(None, max_length=128)
    subspecies: str | None = Field(None, max_length=128)
    authority: str | None = Field(None, max_length=255)
    description: str | None = None
    habitat: str | None = None
    distribution: str | None = None
    altitude_min: int | None = None
    altitude_max: int | None = None
    properties: list[Any] | None = None
    image_url: str | None = None
    identifying_features: list[Any] | None = None
    region: str | None = Field(None, max_length=255)
    category: str | None = Field(None, max_length=128)


class PlantCreate(PlantBase):
    pass


class PlantUpdate(BaseModel):
    scientific_name: str | None = Field(None, max_length=255)
    common_name: str | None = Field(None, max_length=255)
    family: str | None = Field(None, max_length=128)
    genus: str | None = Field(None, max_length=128)
    species: str | None = Field(None, max_length=128)
    subspecies: str | None = Field(None, max_length=128)
    authority: str | None = Field(None, max_length=255)
    description: str | None = None
    habitat: str | None = None
    distribution: str | None = None
    altitude_min: int | None = None
    altitude_max: int | None = None
    properties: list[Any] | None = None
    image_url: str | None = None
    identifying_features: list[Any] | None = None
    region: str | None = Field(None, max_length=255)
    category: str | None = Field(None, max_length=128)


class PlantResponse(BaseModel):
    id: UUID
    scientific_name: str
    common_name: str | None
    family: str | None
    genus: str | None
    status: PlantStatus
    properties: list[Any] | None = None
    image_url: str | None = None
    region: str | None = None
    category: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlantVersionResponse(BaseModel):
    id: UUID
    version_number: int
    change_summary: str | None
    changed_by: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompoundSummary(BaseModel):
    id: UUID
    name: str
    molecular_formula: str | None
    plant_part: str | None

    model_config = {"from_attributes": True}


class ActivitySummary(BaseModel):
    id: UUID
    activity_type: str
    evidence_level: str
    target_condition: str | None

    model_config = {"from_attributes": True}


class PlantDetail(PlantResponse):
    species: str | None
    subspecies: str | None
    authority: str | None
    description: str | None
    habitat: str | None
    distribution: str | None
    altitude_min: int | None
    altitude_max: int | None
    created_by: UUID | None
    reviewed_by: UUID | None
    compounds: list[CompoundSummary] = []
    activities: list[ActivitySummary] = []
    versions: list[PlantVersionResponse] = []


class PlantListResponse(BaseModel):
    items: list[PlantResponse]
    total: int
    page: int
    size: int
    pages: int
