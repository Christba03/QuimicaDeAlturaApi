from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.image_log import (
    ImageLogListResponse,
    ImageLogResponse,
    ImageLogUpdate,
)
from src.services.image_log_service import ImageLogService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> ImageLogService:
    return ImageLogService(session=db)


@router.get("/", response_model=ImageLogListResponse)
async def list_image_logs(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    flagged: bool | None = Query(None, description="Filter by flagged state"),
    service: ImageLogService = Depends(_get_service),
):
    return await service.list_image_logs(page=page, size=size, flagged=flagged)


@router.get("/{item_id}", response_model=ImageLogResponse)
async def get_image_log(
    item_id: UUID,
    service: ImageLogService = Depends(_get_service),
):
    item = await service.get_image_log(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Image log not found")
    return item


@router.put("/{item_id}", response_model=ImageLogResponse)
async def update_image_log(
    item_id: UUID,
    data: ImageLogUpdate,
    service: ImageLogService = Depends(_get_service),
):
    item = await service.update_image_log(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Image log not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_image_log(
    item_id: UUID,
    service: ImageLogService = Depends(_get_service),
):
    deleted = await service.delete_image_log(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image log not found")
