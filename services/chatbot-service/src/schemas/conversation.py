from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    user_id: UUID
    title: str | None = None
    language: str = Field(default="es", pattern="^(es|en)$")


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    intent: str | None = None
    entities: dict | None = None
    feedback_rating: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None = None
    status: str
    language: str
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
