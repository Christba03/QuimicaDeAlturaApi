import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class UserFeedback(str, enum.Enum):
    correct = "correct"
    incorrect = "incorrect"
    unsure = "unsure"


class ImageLog(Base):
    __tablename__ = "image_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_url = Column(String(500), nullable=False)
    predicted_species = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(64), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    flagged = Column(Boolean, nullable=False, default=False)
    user_feedback = Column(Enum(UserFeedback), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ImageLog(id={self.id}, predicted_species={self.predicted_species})>"
