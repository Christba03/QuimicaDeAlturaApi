import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class ExternalApi(Base):
    __tablename__ = "external_apis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    base_url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    auth_type = Column(String(64), nullable=True)
    rate_limit = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    endpoints = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<ExternalApi(id={self.id}, name={self.name})>"
