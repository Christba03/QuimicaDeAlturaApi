import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from src.dependencies import get_db, get_redis
from src.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    UserPreferences,
)
from src.services.profile_service import ProfileService

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., description="Authenticated user ID")) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID header")


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get the current user's profile."""
    service = ProfileService(db, redis)
    return await service.get_profile(user_id)


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update: UserProfileUpdate,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Update the current user's profile."""
    service = ProfileService(db, redis)
    return await service.update_profile(user_id, update)


@router.get("/me/preferences", response_model=UserPreferences)
async def get_my_preferences(
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get the current user's preferences."""
    raw = await redis.get(f"user:preferences:{user_id}")
    if raw:
        return UserPreferences.model_validate_json(raw)
    return UserPreferences()


@router.put("/me/preferences", response_model=UserPreferences)
async def update_my_preferences(
    preferences: UserPreferences,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Update the current user's preferences."""
    service = ProfileService(db, redis)
    return await service.update_preferences(user_id, preferences)
