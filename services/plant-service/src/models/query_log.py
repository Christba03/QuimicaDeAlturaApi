import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    extracted_entities = Column(JSONB, nullable=False, server_default="[]")
    ontology_mappings = Column(JSONB, nullable=False, server_default="[]")
    plants_returned = Column(JSONB, nullable=False, server_default="[]")
    confidence = Column(Float, nullable=True)
    flagged = Column(Boolean, nullable=False, default=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<QueryLog(id={self.id})>"
