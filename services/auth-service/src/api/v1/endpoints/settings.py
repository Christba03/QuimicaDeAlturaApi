from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.settings import AppSettings

router = APIRouter()


class AppSettingsResponse(BaseModel):
    site_name: str
    maintenance_mode: bool
    default_language: str
    max_upload_size_mb: int
    enable_public_api: bool
    contact_email: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    default_language: Optional[str] = None
    max_upload_size_mb: Optional[int] = None
    enable_public_api: Optional[bool] = None
    contact_email: Optional[str] = None


async def _get_or_create_settings(db: AsyncSession) -> AppSettings:
    result = await db.execute(select(AppSettings).limit(1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = AppSettings()
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
    return settings


@router.get("/", response_model=AppSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await _get_or_create_settings(db)


@router.put("/", response_model=AppSettingsResponse)
async def update_settings(
    data: AppSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    settings = await _get_or_create_settings(db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    await db.flush()
    await db.refresh(settings)
    return settings
