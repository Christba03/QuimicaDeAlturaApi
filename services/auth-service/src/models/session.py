import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)

    # --- Refresh token family tracking (reuse detection) ---
    # All sessions issued via the same refresh-token chain share a family_id.
    # When a rotated token is replayed, we invalidate the entire family.
    token_family: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, index=True
    )
    family_invalidated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # --- Device / network ---
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    device_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- GeoIP (enriched at session creation) ---
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    country_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)

    # --- Device trust ---
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    trusted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
