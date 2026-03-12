from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

from src.models.image_log import UserFeedback


class ImageLogResponse(BaseModel):
    id: UUID
    image_url: str
    predicted_species: Optional[str] = None
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    user_id: Optional[UUID] = None
    flagged: bool
    user_feedback: Optional[UserFeedback] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageLogUpdate(BaseModel):
    flagged: Optional[bool] = None
    user_feedback: Optional[UserFeedback] = None


class ImageLogListResponse(BaseModel):
    items: list[ImageLogResponse]
    total: int
    page: int
    size: int
    pages: int
