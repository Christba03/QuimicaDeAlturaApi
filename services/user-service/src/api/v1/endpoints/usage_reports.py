import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from src.dependencies import get_db, get_redis
from src.schemas.usage_report import (
    UsageReportCreate,
    UsageReportResponse,
    UsageReportListResponse,
)
from src.services.usage_report_service import UsageReportService

router = APIRouter()


def _get_user_id(x_user_id: str = Header(...)) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID header")


@router.post("", response_model=UsageReportResponse, status_code=201)
async def submit_usage_report(
    body: UsageReportCreate,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Submit a new plant usage report (user experience)."""
    service = UsageReportService(db, redis)
    return await service.create_report(user_id, body)


@router.get("", response_model=UsageReportListResponse)
async def list_usage_reports(
    plant_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """List usage reports for the current user, optionally filtered by plant."""
    service = UsageReportService(db, redis)
    return await service.list_reports(
        user_id=user_id, plant_id=plant_id, page=page, page_size=page_size
    )


@router.get("/{report_id}", response_model=UsageReportResponse)
async def get_usage_report(
    report_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get a specific usage report by ID."""
    service = UsageReportService(db, redis)
    report = await service.get_report(report_id, user_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Usage report not found")
    return report


@router.delete("/{report_id}", status_code=204)
async def delete_usage_report(
    report_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Delete a usage report."""
    service = UsageReportService(db, redis)
    deleted = await service.delete_report(report_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usage report not found")
