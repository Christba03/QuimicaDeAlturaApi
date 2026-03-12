import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class InferenceJobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    flagged = "flagged"


class InferenceJob(Base):
    __tablename__ = "inference_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species = Column(String(255), nullable=True, index=True)
    job_type = Column(String(128), nullable=False)
    confidence_score = Column(Float, nullable=True)
    output = Column(JSONB, nullable=False, server_default="{}")
    flagged_for_review = Column(Boolean, nullable=False, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(InferenceJobStatus), nullable=False, default=InferenceJobStatus.pending, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<InferenceJob(id={self.id}, job_type={self.job_type}, status={self.status})>"
