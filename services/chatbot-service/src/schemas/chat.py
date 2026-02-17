from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: UUID
    conversation_id: UUID | None = None
    message: str = Field(..., min_length=1, max_length=4000)
    language: str = Field(default="es", pattern="^(es|en)$")


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    response: str
    intent: str | None = None
    entities: list[dict] | None = None
    sources: list[str] | None = None
    suggested_replies: list[str] | None = None
    created_at: datetime


class QuickReply(BaseModel):
    id: str
    label: str
    intent: str


class QuickReplyResponse(BaseModel):
    quick_replies: list[QuickReply]
    language: str


class FeedbackRequest(BaseModel):
    message_id: UUID
    user_id: UUID
    rating: int = Field(..., ge=-1, le=1, description="-1 = thumbs down, 0 = neutral, 1 = thumbs up")
    comment: str | None = None


class FeedbackResponse(BaseModel):
    message_id: UUID
    rating: int
    comment: str | None = None
    recorded_at: datetime


class FeedbackStatsResponse(BaseModel):
    total_feedback: int
    positive: int
    negative: int
    neutral: int
    positive_rate: float
    period_days: int
