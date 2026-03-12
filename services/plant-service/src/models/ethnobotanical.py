import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class EvidenceLevel(str, enum.Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class EthnobotanicalRecord(Base):
    __tablename__ = "ethnobotanical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species = Column(String(255), nullable=False, index=True)
    community = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True, index=True)
    condition_treated = Column(String(255), nullable=True)
    preparation_method = Column(Text, nullable=True)
    raw_material_part = Column(String(128), nullable=True)
    documenter = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    evidence_level = Column(Enum(EvidenceLevel), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<EthnobotanicalRecord(id={self.id}, species={self.species})>"
