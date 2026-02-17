import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.plant import Base


class EvidenceLevel(str, enum.Enum):
    TRADITIONAL = "traditional"
    IN_VITRO = "in_vitro"
    IN_VIVO = "in_vivo"
    CLINICAL_TRIAL = "clinical_trial"
    SYSTEMATIC_REVIEW = "systematic_review"


class MedicinalActivity(Base):
    __tablename__ = "medicinal_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id = Column(
        UUID(as_uuid=True), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False
    )
    activity_type = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    evidence_level = Column(
        Enum(EvidenceLevel),
        nullable=False,
        default=EvidenceLevel.TRADITIONAL,
    )
    target_condition = Column(String(255), nullable=True)
    mechanism_of_action = Column(Text, nullable=True)
    dosage_info = Column(Text, nullable=True)
    side_effects = Column(Text, nullable=True)
    contraindications = Column(Text, nullable=True)
    reference_doi = Column(String(255), nullable=True)
    reference_pubmed_id = Column(String(32), nullable=True)
    reference_title = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    plant = relationship("Plant", back_populates="activities")

    def __repr__(self) -> str:
        return f"<MedicinalActivity(id={self.id}, type={self.activity_type})>"
