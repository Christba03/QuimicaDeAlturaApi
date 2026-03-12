import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Text, DateTime, Integer, Float, func, Index, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.favorite import Base


class EffectivenessRating(str, PyEnum):
    NOT_EFFECTIVE = "not_effective"
    SLIGHTLY_EFFECTIVE = "slightly_effective"
    MODERATELY_EFFECTIVE = "moderately_effective"
    VERY_EFFECTIVE = "very_effective"
    EXTREMELY_EFFECTIVE = "extremely_effective"


class UserPlantUsageReport(Base):
    __tablename__ = "user_plant_usage_reports"
    __table_args__ = (
        Index("ix_usage_reports_user_id", "user_id"),
        Index("ix_usage_reports_plant_id", "plant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    effectiveness: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    dosage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dosage_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preparation_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    side_effects_list: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    condition_treated: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    altitude_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<UserPlantUsageReport(user={self.user_id}, plant={self.plant_id}, "
            f"effectiveness={self.effectiveness})>"
        )
