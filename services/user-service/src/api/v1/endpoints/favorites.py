import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from src.dependencies import get_db, get_redis
from src.repositories.user_repository import UserRepository

router = APIRouter()


class FavoriteCreate(BaseModel):
    plant_id: uuid.UUID
    notes: Optional[str] = None
    category: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    plant_id: uuid.UUID
    notes: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteListResponse(BaseModel):
    items: list[FavoriteResponse]
    total: int
    page: int
    page_size: int


def _get_user_id(x_user_id: str = Header(...)) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID header")


@router.get("", response_model=FavoriteListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's favorite plants."""
    repo = UserRepository(db)
    offset = (page - 1) * page_size
    rows, total = await repo.get_favorites(user_id, offset=offset, limit=page_size)
    items = [FavoriteResponse.model_validate(r) for r in rows]
    return FavoriteListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=FavoriteResponse, status_code=201)
async def add_favorite(
    body: FavoriteCreate,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Add a plant to the user's favorites."""
    repo = UserRepository(db)
    if await repo.is_favorite(user_id, body.plant_id):
        raise HTTPException(status_code=409, detail="Plant is already a favorite")

    fav = await repo.add_favorite(
        user_id=user_id,
        plant_id=body.plant_id,
        notes=body.notes,
        category=body.category,
    )
    await redis.delete(f"user:profile:{user_id}")
    return FavoriteResponse.model_validate(fav)


@router.delete("/{plant_id}", status_code=204)
async def remove_favorite(
    plant_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Remove a plant from the user's favorites."""
    repo = UserRepository(db)
    removed = await repo.remove_favorite(user_id, plant_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorite not found")
    await redis.delete(f"user:profile:{user_id}")


@router.get("/{plant_id}/check")
async def check_favorite(
    plant_id: uuid.UUID,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Check if a plant is in the user's favorites."""
    repo = UserRepository(db)
    is_fav = await repo.is_favorite(user_id, plant_id)
    return {"is_favorite": is_fav}
