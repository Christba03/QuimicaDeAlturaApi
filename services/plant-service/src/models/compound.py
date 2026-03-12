import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.models.plant import Base


class ChemicalCompound(Base):
    __tablename__ = "chemical_compounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    iupac_name = Column(String(512), nullable=True)
    molecular_formula = Column(String(128), nullable=True)
    molecular_weight = Column(Float, nullable=True)
    cas_number = Column(String(32), nullable=True, unique=True, index=True)
    pubchem_cid = Column(String(32), nullable=True, index=True)
    inchi_key = Column(String(64), nullable=True, unique=True)
    smiles = Column(Text, nullable=True)
    inchi = Column(Text, nullable=True)
    compound_class = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)
    properties = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plants = relationship(
        "PlantCompound", back_populates="compound", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChemicalCompound(id={self.id}, name={self.name})>"


class PlantCompound(Base):
    __tablename__ = "plant_compounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(
        UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    compound_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chemical_compounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    plant_part = Column(String(64), nullable=True)  # root, leaf, flower, etc.
    concentration = Column(String(64), nullable=True)
    extraction_method = Column(String(128), nullable=True)
    reference = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plant = relationship("Plant", back_populates="compounds")
    compound = relationship("ChemicalCompound", back_populates="plants")

    def __repr__(self) -> str:
        return f"<PlantCompound(plant_id={self.plant_id}, compound_id={self.compound_id})>"
