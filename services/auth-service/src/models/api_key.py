import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base


class APIKey(Base):
    """Machine-to-machine API keys for service accounts and CLI tools."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)          # human-friendly label
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)     # first 8 chars for display ("mpa_xxxx")
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hex

    # Comma-style scopes list stored as a PostgreSQL text array
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, prefix={self.key_prefix}, user_id={self.user_id})>"
