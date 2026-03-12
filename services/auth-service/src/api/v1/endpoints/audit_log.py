"""
Audit log endpoint — exposes SecurityEvent records via /api/audit-log.
Maps SecurityEvent fields to the dashboard AuditLog shape.
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.security_event import SecurityEvent

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    user_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    changes: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": False}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    size: int
    pages: int


def _map_event(event: SecurityEvent) -> AuditLogResponse:
    meta = event.event_metadata or {}
    return AuditLogResponse(
        id=event.id,
        action=event.event_type.value,
        user_id=event.user_id,
        ip_address=event.ip_address,
        resource=meta.get("resource"),
        resource_id=meta.get("resource_id") or meta.get("resourceId"),
        changes=meta.get("changes"),
        created_at=event.created_at,
    )


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_log(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    action: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    import math

    stmt = select(SecurityEvent)
    count_stmt = select(func.count(SecurityEvent.id))

    if action:
        stmt = stmt.where(SecurityEvent.event_type == action)
        count_stmt = count_stmt.where(SecurityEvent.event_type == action)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(SecurityEvent.created_at.desc()).offset((page - 1) * size).limit(size)
    events = list((await db.execute(stmt)).scalars().all())
    pages = math.ceil(total / size) if total > 0 else 0

    return AuditLogListResponse(
        items=[_map_event(e) for e in events],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{event_id}", response_model=AuditLogResponse)
async def get_audit_log(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Audit log entry not found")
    return _map_event(event)
