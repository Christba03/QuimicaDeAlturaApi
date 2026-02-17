from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.models.activity import EvidenceLevel, MedicinalActivity

router = APIRouter()


class ActivityCreate(BaseModel):
    plant_id: UUID
    activity_type: str = Field(..., max_length=128)
    description: str | None = None
    evidence_level: EvidenceLevel = EvidenceLevel.TRADITIONAL
    target_condition: str | None = Field(None, max_length=255)
    mechanism_of_action: str | None = None
    dosage_info: str | None = None
    side_effects: str | None = None
    contraindications: str | None = None
    reference_doi: str | None = Field(None, max_length=255)
    reference_pubmed_id: str | None = Field(None, max_length=32)
    reference_title: str | None = None


class ActivityUpdate(BaseModel):
    activity_type: str | None = Field(None, max_length=128)
    description: str | None = None
    evidence_level: EvidenceLevel | None = None
    target_condition: str | None = Field(None, max_length=255)
    mechanism_of_action: str | None = None
    dosage_info: str | None = None
    side_effects: str | None = None
    contraindications: str | None = None
    reference_doi: str | None = Field(None, max_length=255)
    reference_pubmed_id: str | None = Field(None, max_length=32)
    reference_title: str | None = None


class ActivityResponse(BaseModel):
    id: UUID
    plant_id: UUID
    activity_type: str
    description: str | None
    evidence_level: EvidenceLevel
    target_condition: str | None
    mechanism_of_action: str | None
    dosage_info: str | None
    side_effects: str | None
    contraindications: str | None
    reference_doi: str | None
    reference_pubmed_id: str | None
    reference_title: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    size: int


@router.get("/", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    plant_id: UUID | None = Query(None, description="Filter by plant"),
    activity_type: str | None = Query(None, description="Filter by activity type"),
    evidence_level: EvidenceLevel | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicinalActivity)
    count_stmt = select(func.count(MedicinalActivity.id))

    if plant_id:
        stmt = stmt.where(MedicinalActivity.plant_id == plant_id)
        count_stmt = count_stmt.where(MedicinalActivity.plant_id == plant_id)

    if activity_type:
        stmt = stmt.where(MedicinalActivity.activity_type.ilike(f"%{activity_type}%"))
        count_stmt = count_stmt.where(
            MedicinalActivity.activity_type.ilike(f"%{activity_type}%")
        )

    if evidence_level:
        stmt = stmt.where(MedicinalActivity.evidence_level == evidence_level)
        count_stmt = count_stmt.where(
            MedicinalActivity.evidence_level == evidence_level
        )

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    activities = list(result.scalars().all())

    return ActivityListResponse(
        items=activities, total=total, page=page, size=size
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicinalActivity).where(MedicinalActivity.id == activity_id)
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.post("/", response_model=ActivityResponse, status_code=201)
async def create_activity(
    data: ActivityCreate,
    db: AsyncSession = Depends(get_db),
):
    activity = MedicinalActivity(**data.model_dump())
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    data: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicinalActivity).where(MedicinalActivity.id == activity_id)
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(activity, key, value)

    await db.commit()
    await db.refresh(activity)
    return activity


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MedicinalActivity).where(MedicinalActivity.id == activity_id)
    result = await db.execute(stmt)
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(activity)
    await db.commit()
