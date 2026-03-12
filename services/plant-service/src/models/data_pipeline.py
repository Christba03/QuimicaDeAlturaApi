import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class PipelineStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    error = "error"
    syncing = "syncing"


class DataPipeline(Base):
    __tablename__ = "data_pipelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    source = Column(String(255), nullable=True)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    next_sync = Column(DateTime(timezone=True), nullable=True)
    records_synced = Column(Integer, nullable=False, default=0)
    error_log = Column(Text, nullable=True)
    status = Column(Enum(PipelineStatus), nullable=False, default=PipelineStatus.idle, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<DataPipeline(id={self.id}, name={self.name}, status={self.status})>"
