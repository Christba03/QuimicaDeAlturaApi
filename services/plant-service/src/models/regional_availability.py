import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from src.models.plant import Base


class AbundanceLevel(str, enum.Enum):
    common = "common"
    scarce = "scarce"
    rare = "rare"


class RegionalAvailability(Base):
    __tablename__ = "regional_availability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    species = Column(String(255), nullable=False, index=True)
    state = Column(String(128), nullable=True, index=True)
    region = Column(String(255), nullable=True, index=True)
    source = Column(String(255), nullable=True)
    abundance = Column(Enum(AbundanceLevel), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<RegionalAvailability(id={self.id}, species={self.species}, state={self.state})>"
