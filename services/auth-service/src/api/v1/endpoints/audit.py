"""
Audit log API — exposes the SecurityEvent table.

  GET /api/v1/audit/events                     — all events (admin)
  GET /api/v1/audit/users/{user_id}/events     — events for a specific user
"""
import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user, require_superuser
from src.main import get_db
from src.models.security_event import SecurityEvent, SecurityEventType

logger = structlog.get_logger()
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SecurityEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: SecurityEventType
    ip_address: str | None
    user_agent: str | None
    metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityEventListResponse(BaseModel):
    events: list[SecurityEventResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_db_session(session: AsyncSession = Depends(get_db)) -> AsyncSession:
    return session


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/events", response_model=SecurityEventListResponse)
async def list_all_security_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: SecurityEventType | None = Query(None),
    since: datetime | None = Query(None, description="ISO 8601 — only events after this timestamp"),
    until: datetime | None = Query(None, description="ISO 8601 — only events before this timestamp"),
    ip_address: str | None = Query(None),
    _: dict = Depends(require_superuser),
    session: AsyncSession = Depends(get_db_session),
):
    """List all security events (admin endpoint). Paginated and filterable."""
    stmt = select(SecurityEvent)
    count_stmt = select(func.count()).select_from(SecurityEvent)

    if event_type:
        stmt = stmt.where(SecurityEvent.event_type == event_type)
        count_stmt = count_stmt.where(SecurityEvent.event_type == event_type)
    if since:
        stmt = stmt.where(SecurityEvent.created_at >= since)
        count_stmt = count_stmt.where(SecurityEvent.created_at >= since)
    if until:
        stmt = stmt.where(SecurityEvent.created_at <= until)
        count_stmt = count_stmt.where(SecurityEvent.created_at <= until)
    if ip_address:
        stmt = stmt.where(SecurityEvent.ip_address == ip_address)
        count_stmt = count_stmt.where(SecurityEvent.ip_address == ip_address)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(SecurityEvent.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    events = list(result.scalars().all())

    return SecurityEventListResponse(events=events, total=total, page=page, page_size=page_size)


@router.get("/users/{user_id}/events", response_model=SecurityEventListResponse)
async def list_user_security_events(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: SecurityEventType | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List security events for a specific user. Accessible by the user and admins."""
    # Users can only see their own events; admins can see any user's events
    is_admin = "admin" in current_user.get("roles", []) or current_user.get("is_superuser")
    if str(user_id) != current_user.get("sub") and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    base_filter = SecurityEvent.user_id == user_id

    count_stmt = select(func.count()).select_from(SecurityEvent).where(base_filter)
    stmt = select(SecurityEvent).where(base_filter)

    if event_type:
        stmt = stmt.where(SecurityEvent.event_type == event_type)
        count_stmt = count_stmt.where(SecurityEvent.event_type == event_type)
    if since:
        stmt = stmt.where(SecurityEvent.created_at >= since)
        count_stmt = count_stmt.where(SecurityEvent.created_at >= since)
    if until:
        stmt = stmt.where(SecurityEvent.created_at <= until)
        count_stmt = count_stmt.where(SecurityEvent.created_at <= until)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(SecurityEvent.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(stmt)
    events = list(result.scalars().all())

    return SecurityEventListResponse(events=events, total=total, page=page, page_size=page_size)
