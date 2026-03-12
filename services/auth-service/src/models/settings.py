import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from src.models import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_name = Column(String(255), nullable=False, default="Quimica de Altura")
    maintenance_mode = Column(Boolean, nullable=False, default=False)
    default_language = Column(String(10), nullable=False, default="es")
    max_upload_size_mb = Column(Integer, nullable=False, default=10)
    enable_public_api = Column(Boolean, nullable=False, default=True)
    contact_email = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<AppSettings(id={self.id}, site_name={self.site_name})>"
