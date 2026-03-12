import json
import uuid

import structlog
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.user_repository import UserRepository
from src.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    UserPreferences,
)

logger = structlog.get_logger(__name__)

PROFILE_CACHE_TTL = 300  # 5 minutes
PROFILE_KEY_PREFIX = "user:profile:"


class ProfileService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis):
        self.repo = UserRepository(session)
        self.redis = redis

    async def get_profile(self, user_id: uuid.UUID) -> UserProfileResponse:
        cache_key = f"{PROFILE_KEY_PREFIX}{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug("Profile cache hit", user_id=str(user_id))
            return UserProfileResponse.model_validate_json(cached)

        favorites_count = await self.repo.get_favorites_count(user_id)
        reports_count = await self.repo.get_reports_count(user_id)

        prefs_raw = await self.redis.get(f"user:preferences:{user_id}")
        preferences = (
            UserPreferences.model_validate_json(prefs_raw)
            if prefs_raw
            else UserPreferences()
        )

        profile_raw = await self.redis.hgetall(f"user:data:{user_id}")

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        profile = UserProfileResponse(
            id=user_id,
            email=profile_raw.get("email"),
            display_name=profile_raw.get("display_name"),
            bio=profile_raw.get("bio"),
            location=profile_raw.get("location"),
            altitude_meters=float(profile_raw["altitude_meters"])
            if profile_raw.get("altitude_meters")
            else None,
            expertise_level=profile_raw.get("expertise_level", "beginner"),
            birthdate=profile_raw.get("birthdate"),
            nationality=profile_raw.get("nationality"),
            address=profile_raw.get("address"),
            preferences=preferences,
            favorites_count=favorites_count,
            reports_count=reports_count,
            created_at=datetime.fromisoformat(profile_raw["created_at"])
            if profile_raw.get("created_at")
            else now,
            updated_at=datetime.fromisoformat(profile_raw["updated_at"])
            if profile_raw.get("updated_at")
            else now,
        )

        await self.redis.set(
            cache_key,
            profile.model_dump_json(),
            ex=PROFILE_CACHE_TTL,
        )
        return profile

    async def update_profile(
        self, user_id: uuid.UUID, update: UserProfileUpdate
    ) -> UserProfileResponse:
        from datetime import datetime, timezone

        data_key = f"user:data:{user_id}"
        update_dict = update.model_dump(exclude_none=True, exclude={"preferences"})
        if update_dict:
            update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.redis.hset(data_key, mapping={k: str(v) for k, v in update_dict.items()})

        if update.preferences is not None:
            await self.redis.set(
                f"user:preferences:{user_id}",
                update.preferences.model_dump_json(),
            )

        # Invalidate cache
        await self.redis.delete(f"{PROFILE_KEY_PREFIX}{user_id}")
        logger.info("Profile updated", user_id=str(user_id))

        return await self.get_profile(user_id)

    async def update_preferences(
        self, user_id: uuid.UUID, preferences: UserPreferences
    ) -> UserPreferences:
        await self.redis.set(
            f"user:preferences:{user_id}",
            preferences.model_dump_json(),
        )
        await self.redis.delete(f"{PROFILE_KEY_PREFIX}{user_id}")
        logger.info("Preferences updated", user_id=str(user_id))
        return preferences
