from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.query_log import (
    QueryLogFlagUpdate,
    QueryLogListResponse,
    QueryLogResponse,
)
from src.services.query_log_service import QueryLogService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> QueryLogService:
    return QueryLogService(session=db)


@router.get("/", response_model=QueryLogListResponse)
async def list_query_logs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    flagged: bool | None = Query(None, description="Filter by flagged state"),
    service: QueryLogService = Depends(_get_service),
):
    return await service.list_query_logs(page=page, size=size, flagged=flagged)


@router.get("/{item_id}", response_model=QueryLogResponse)
async def get_query_log(
    item_id: UUID,
    service: QueryLogService = Depends(_get_service),
):
    item = await service.get_query_log(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Query log not found")
    return item


@router.put("/{item_id}", response_model=QueryLogResponse)
async def update_query_log(
    item_id: UUID,
    data: QueryLogFlagUpdate,
    service: QueryLogService = Depends(_get_service),
):
    item = await service.update_query_log(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Query log not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_query_log(
    item_id: UUID,
    service: QueryLogService = Depends(_get_service),
):
    deleted = await service.delete_query_log(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query log not found")
