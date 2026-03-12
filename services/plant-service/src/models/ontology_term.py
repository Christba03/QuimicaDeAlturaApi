import uuid

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.models.plant import Base


class OntologyTerm(Base):
    __tablename__ = "ontology_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_term = Column(String(255), nullable=False, unique=True, index=True)
    icd10_code = Column(String(32), nullable=True)
    mesh_id = Column(String(64), nullable=True)
    synonyms = Column(JSONB, nullable=False, server_default="[]")
    category = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<OntologyTerm(id={self.id}, canonical_term={self.canonical_term})>"
