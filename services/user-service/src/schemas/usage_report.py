import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.models.usage_report import EffectivenessRating


class UsageReportCreate(BaseModel):
    plant_id: uuid.UUID
    effectiveness: EffectivenessRating
    rating: int = Field(ge=1, le=5, default=3, description="Rating from 1 to 5")
    dosage: Optional[str] = None
    dosage_unit: Optional[str] = None
    frequency: Optional[str] = Field(default=None, description="e.g. twice daily, weekly")
    duration_days: Optional[int] = Field(default=None, ge=1)
    preparation_method: Optional[str] = Field(
        default=None, description="e.g. infusion, decoction, tincture, poultice"
    )
    side_effects: Optional[str] = None
    side_effects_list: Optional[list[str]] = None
    condition_treated: Optional[str] = None
    notes: Optional[str] = None
    altitude_meters: Optional[float] = Field(default=None, ge=0)


class UsageReportUpdate(BaseModel):
    effectiveness: Optional[EffectivenessRating] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    dosage: Optional[str] = None
    dosage_unit: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = Field(default=None, ge=1)
    preparation_method: Optional[str] = None
    side_effects: Optional[str] = None
    side_effects_list: Optional[list[str]] = None
    condition_treated: Optional[str] = None
    notes: Optional[str] = None
    altitude_meters: Optional[float] = Field(default=None, ge=0)


class UsageReportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plant_id: uuid.UUID
    effectiveness: EffectivenessRating
    rating: int
    dosage: Optional[str] = None
    dosage_unit: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    preparation_method: Optional[str] = None
    side_effects: Optional[str] = None
    side_effects_list: Optional[list[str]] = None
    condition_treated: Optional[str] = None
    notes: Optional[str] = None
    altitude_meters: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UsageReportListResponse(BaseModel):
    items: list[UsageReportResponse]
    total: int
    page: int
    page_size: int
