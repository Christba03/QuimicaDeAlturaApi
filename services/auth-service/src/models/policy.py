"""
ABAC (Attribute-Based Access Control) policy model.

A policy grants (or denies) a subject matching a set of conditions
the ability to perform an action on a resource type.

Example policies:
  - subject_type=role,    subject_id=admin,        resource=*,       action=*,      effect=allow
  - subject_type=user,    subject_id=<uuid>,       resource=report,  action=read,   effect=allow,  condition={"owner": true}
  - subject_type=role,    subject_id=analyst,      resource=sample,  action=read,   effect=allow
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who this policy applies to
    subject_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # "user" | "role"
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)   # UUID str or role name; "*" = all

    # What resource type (e.g. "sample", "report", "*")
    resource: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # What action (e.g. "read", "write", "delete", "*")
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # "allow" | "deny"  (deny takes precedence)
    effect: Mapped[str] = mapped_column(String(10), nullable=False, default="allow")

    # Optional JSON conditions evaluated at runtime:
    # {"owner": true}          → resource.owner_id must equal subject user_id
    # {"min_role_score": 2}    → subject must have a role with score >= 2
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Policy({self.subject_type}:{self.subject_id} "
            f"{self.effect} {self.action} on {self.resource})>"
        )
