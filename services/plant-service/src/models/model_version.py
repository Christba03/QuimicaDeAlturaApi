import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class ModelStatus(str, enum.Enum):
    active = "active"
    deprecated = "deprecated"
    testing = "testing"


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    accuracy = Column(Float, nullable=True)
    type = Column(String(128), nullable=True)
    status = Column(Enum(ModelStatus), nullable=False, default=ModelStatus.testing, index=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    can_rollback = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.id}, name={self.name}, version={self.version})>"
