from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CompoundBase(BaseModel):
    name: str = Field(..., max_length=255)
    iupac_name: str | None = Field(None, max_length=512)
    molecular_formula: str | None = Field(None, max_length=128)
    molecular_weight: float | None = None
    cas_number: str | None = Field(None, max_length=32)
    pubchem_cid: str | None = Field(None, max_length=32)
    inchi_key: str | None = Field(None, max_length=64)
    smiles: str | None = None
    compound_class: str | None = Field(None, max_length=128)
    description: str | None = None


class CompoundCreate(CompoundBase):
    pass


class CompoundUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    iupac_name: str | None = Field(None, max_length=512)
    molecular_formula: str | None = Field(None, max_length=128)
    molecular_weight: float | None = None
    cas_number: str | None = Field(None, max_length=32)
    pubchem_cid: str | None = Field(None, max_length=32)
    inchi_key: str | None = Field(None, max_length=64)
    smiles: str | None = None
    compound_class: str | None = Field(None, max_length=128)
    description: str | None = None


class CompoundResponse(CompoundBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlantCompoundCreate(BaseModel):
    plant_id: UUID
    compound_id: UUID
    plant_part: str | None = Field(None, max_length=64)
    concentration: str | None = Field(None, max_length=64)
    extraction_method: str | None = Field(None, max_length=128)
    reference: str | None = None


class PlantCompoundResponse(BaseModel):
    id: UUID
    plant_id: UUID
    compound_id: UUID
    plant_part: str | None
    concentration: str | None
    extraction_method: str | None
    reference: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompoundListResponse(BaseModel):
    items: list[CompoundResponse]
    total: int
    page: int
    size: int
    pages: int
