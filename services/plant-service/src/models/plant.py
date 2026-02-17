import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class PlantStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Plant(Base):
    __tablename__ = "plants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scientific_name = Column(String(255), nullable=False, unique=True, index=True)
    common_name = Column(String(255), nullable=True, index=True)
    family = Column(String(128), nullable=True, index=True)
    genus = Column(String(128), nullable=True)
    species = Column(String(128), nullable=True)
    subspecies = Column(String(128), nullable=True)
    authority = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    habitat = Column(Text, nullable=True)
    distribution = Column(Text, nullable=True)
    altitude_min = Column(Integer, nullable=True)
    altitude_max = Column(Integer, nullable=True)
    status = Column(
        Enum(PlantStatus), nullable=False, default=PlantStatus.DRAFT, index=True
    )
    created_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    versions = relationship(
        "PlantVersion", back_populates="plant", cascade="all, delete-orphan"
    )
    compounds = relationship(
        "PlantCompound", back_populates="plant", cascade="all, delete-orphan"
    )
    activities = relationship(
        "MedicinalActivity", back_populates="plant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Plant(id={self.id}, scientific_name={self.scientific_name})>"


class PlantVersion(Base):
    __tablename__ = "plant_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(
        UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    data_snapshot = Column(Text, nullable=False)  # JSON snapshot
    change_summary = Column(Text, nullable=True)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plant = relationship("Plant", back_populates="versions")

    def __repr__(self) -> str:
        return f"<PlantVersion(plant_id={self.plant_id}, version={self.version_number})>"
