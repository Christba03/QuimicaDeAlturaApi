import uuid

from sqlalchemy import Column, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class DrugReference(Base):
    __tablename__ = "drug_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drug_name = Column(String(255), nullable=False, index=True)
    active_ingredient = Column(String(255), nullable=True)
    linked_compound = Column(UUID(as_uuid=True), nullable=True)
    linked_plant = Column(UUID(as_uuid=True), nullable=True)
    pathway_overlap = Column(Text, nullable=True)
    similarity_score = Column(Float, nullable=True)
    mechanism = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<DrugReference(id={self.id}, drug_name={self.drug_name})>"
