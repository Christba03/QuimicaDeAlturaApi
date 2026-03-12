from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel

from src.models.inference_job import InferenceJobStatus


class InferenceJobBase(BaseModel):
    species: Optional[str] = None
    job_type: str
    confidence_score: Optional[float] = None
    output: Optional[dict[str, Any]] = None
    flagged_for_review: bool = False
    approved_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    status: Optional[InferenceJobStatus] = InferenceJobStatus.pending


class InferenceJobCreate(InferenceJobBase):
    pass


class InferenceJobUpdate(BaseModel):
    species: Optional[str] = None
    job_type: Optional[str] = None
    confidence_score: Optional[float] = None
    output: Optional[dict[str, Any]] = None
    flagged_for_review: Optional[bool] = None
    approved_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    status: Optional[InferenceJobStatus] = None


class InferenceJobResponse(InferenceJobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InferenceJobListResponse(BaseModel):
    items: list[InferenceJobResponse]
    total: int
    page: int
    size: int
    pages: int
