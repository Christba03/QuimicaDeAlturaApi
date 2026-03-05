import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
import redis.asyncio as aioredis

from src.dependencies import get_redis

router = APIRouter()

SEARCH_HISTORY_KEY = "user:{user_id}:search_history"
VIEW_HISTORY_KEY = "user:{user_id}:view_history"
MAX_HISTORY_SIZE = 200


class SearchHistoryEntry(BaseModel):
    query: str
    filters: dict | None = None
    timestamp: str


class PlantViewEntry(BaseModel):
    plant_id: str
    plant_name: str | None = None
    timestamp: str


class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryEntry]
    total: int


class ViewHistoryResponse(BaseModel):
    items: list[PlantViewEntry]
    total: int


def _get_user_id(x_user_id: str = Header(...)) -> uuid.UUID:
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID header")


@router.get("/searches", response_model=SearchHistoryResponse)
async def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get the user's recent search history."""
    key = SEARCH_HISTORY_KEY.format(user_id=user_id)
    raw_items = await redis.lrange(key, 0, limit - 1)
    items = [SearchHistoryEntry.model_validate_json(item) for item in raw_items]
    total = await redis.llen(key)
    return SearchHistoryResponse(items=items, total=total)


@router.post("/searches", status_code=201)
async def record_search(
    entry: SearchHistoryEntry,
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Record a search query in the user's history."""
    key = SEARCH_HISTORY_KEY.format(user_id=user_id)
    await redis.lpush(key, entry.model_dump_json())
    await redis.ltrim(key, 0, MAX_HISTORY_SIZE - 1)
    return {"status": "recorded"}


@router.delete("/searches", status_code=204)
async def clear_search_history(
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Clear the user's search history."""
    key = SEARCH_HISTORY_KEY.format(user_id=user_id)
    await redis.delete(key)


@router.get("/views", response_model=ViewHistoryResponse)
async def get_view_history(
    limit: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Get the user's plant view history."""
    key = VIEW_HISTORY_KEY.format(user_id=user_id)
    raw_items = await redis.lrange(key, 0, limit - 1)
    items = [PlantViewEntry.model_validate_json(item) for item in raw_items]
    total = await redis.llen(key)
    return ViewHistoryResponse(items=items, total=total)


@router.post("/views", status_code=201)
async def record_plant_view(
    entry: PlantViewEntry,
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Record a plant view in the user's history."""
    key = VIEW_HISTORY_KEY.format(user_id=user_id)
    await redis.lpush(key, entry.model_dump_json())
    await redis.ltrim(key, 0, MAX_HISTORY_SIZE - 1)
    return {"status": "recorded"}


@router.delete("/views", status_code=204)
async def clear_view_history(
    user_id: uuid.UUID = Depends(_get_user_id),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Clear the user's plant view history."""
    key = VIEW_HISTORY_KEY.format(user_id=user_id)
    await redis.delete(key)
