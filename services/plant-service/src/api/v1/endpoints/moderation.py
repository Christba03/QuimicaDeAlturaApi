from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.moderation import (
    ModerationApproveRequest,
    ModerationCreate,
    ModerationListResponse,
    ModerationRejectRequest,
    ModerationResponse,
    ModerationUpdate,
)
from src.services.moderation_service import ModerationService

router = APIRouter()


async def _get_service(
    db: AsyncSession = Depends(get_db),
) -> ModerationService:
    return ModerationService(session=db)


@router.get("/", response_model=ModerationListResponse)
async def list_moderation_items(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by moderation status"),
    service: ModerationService = Depends(_get_service),
):
    return await service.list_moderation_items(page=page, size=size, status=status)


@router.get("/{item_id}", response_model=ModerationResponse)
async def get_moderation_item(
    item_id: UUID,
    service: ModerationService = Depends(_get_service),
):
    item = await service.get_moderation_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.post("/", response_model=ModerationResponse, status_code=201)
async def create_moderation_item(
    data: ModerationCreate,
    service: ModerationService = Depends(_get_service),
):
    return await service.create_moderation_item(data)


@router.put("/{item_id}", response_model=ModerationResponse)
async def update_moderation_item(
    item_id: UUID,
    data: ModerationUpdate,
    service: ModerationService = Depends(_get_service),
):
    item = await service.update_moderation_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_moderation_item(
    item_id: UUID,
    service: ModerationService = Depends(_get_service),
):
    deleted = await service.delete_moderation_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")


@router.put("/{item_id}/approve", response_model=ModerationResponse)
async def approve_item(item_id: UUID, body: ModerationApproveRequest, service: ModerationService = Depends(_get_service)):
    item = await service.approve_item(item_id, body.reviewer_id, body.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.put("/{item_id}/reject", response_model=ModerationResponse)
async def reject_item(item_id: UUID, body: ModerationRejectRequest, service: ModerationService = Depends(_get_service)):
    item = await service.reject_item(item_id, body.reviewer_id, body.notes)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
