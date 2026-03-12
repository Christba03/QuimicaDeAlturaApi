import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class ModerationItemType(str, enum.Enum):
    record = "record"
    correction = "correction"
    submission = "submission"


class ModerationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ModerationItem(Base):
    __tablename__ = "moderation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(ModerationItemType), nullable=False)
    content = Column(JSONB, nullable=False, server_default="{}")
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(ModerationStatus), nullable=False, default=ModerationStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<ModerationItem(id={self.id}, type={self.type}, status={self.status})>"
