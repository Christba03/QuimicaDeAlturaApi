from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel

from src.models.moderation import ModerationItemType, ModerationStatus


class ModerationBase(BaseModel):
    type: ModerationItemType
    content: Optional[dict[str, Any]] = None
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    notes: Optional[str] = None


class ModerationCreate(ModerationBase):
    pass


class ModerationUpdate(BaseModel):
    type: Optional[ModerationItemType] = None
    content: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    status: Optional[ModerationStatus] = None


class ModerationResponse(ModerationBase):
    id: UUID
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    status: ModerationStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModerationListResponse(BaseModel):
    items: list[ModerationResponse]
    total: int
    page: int
    size: int
    pages: int


class ModerationApproveRequest(BaseModel):
    reviewer_id: Optional[UUID] = None
    notes: Optional[str] = None


class ModerationRejectRequest(BaseModel):
    reviewer_id: Optional[UUID] = None
    notes: Optional[str] = None
