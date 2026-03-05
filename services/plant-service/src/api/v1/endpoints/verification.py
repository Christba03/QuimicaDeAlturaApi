from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db, get_redis
from src.core.events import EventPublisher
from src.models.plant import PlantStatus
from src.schemas.plant import PlantResponse
from src.services.verification_service import VerificationService

router = APIRouter()


class VerificationAction(BaseModel):
    reviewer_id: UUID


class RejectionAction(BaseModel):
    reviewer_id: UUID
    reason: str | None = None


class VerificationStatusResponse(BaseModel):
    plant_id: UUID
    status: PlantStatus
    message: str


async def _get_verification_service(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> VerificationService:
    events = EventPublisher(redis) if redis else None
    return VerificationService(session=db, events=events)


@router.post(
    "/{plant_id}/submit",
    response_model=VerificationStatusResponse,
)
async def submit_for_review(
    plant_id: UUID,
    service: VerificationService = Depends(_get_verification_service),
):
    try:
        plant = await service.submit_for_review(plant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    return VerificationStatusResponse(
        plant_id=plant.id,
        status=plant.status,
        message="Plant submitted for review successfully.",
    )


@router.post(
    "/{plant_id}/approve",
    response_model=VerificationStatusResponse,
)
async def approve_plant(
    plant_id: UUID,
    action: VerificationAction,
    service: VerificationService = Depends(_get_verification_service),
):
    try:
        plant = await service.approve(plant_id, action.reviewer_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    return VerificationStatusResponse(
        plant_id=plant.id,
        status=plant.status,
        message="Plant approved and verified.",
    )


@router.post(
    "/{plant_id}/reject",
    response_model=VerificationStatusResponse,
)
async def reject_plant(
    plant_id: UUID,
    action: RejectionAction,
    service: VerificationService = Depends(_get_verification_service),
):
    try:
        plant = await service.reject(plant_id, action.reviewer_id, action.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    return VerificationStatusResponse(
        plant_id=plant.id,
        status=plant.status,
        message="Plant has been rejected.",
    )


@router.post(
    "/{plant_id}/revert",
    response_model=VerificationStatusResponse,
)
async def revert_to_draft(
    plant_id: UUID,
    service: VerificationService = Depends(_get_verification_service),
):
    try:
        plant = await service.revert_to_draft(plant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    return VerificationStatusResponse(
        plant_id=plant.id,
        status=plant.status,
        message="Plant reverted to draft status.",
    )
