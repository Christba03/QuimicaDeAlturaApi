import json
from uuid import UUID

import structlog
from redis.asyncio import Redis

from src.config import get_settings

logger = structlog.get_logger()


class PlantCache:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "plant-service:plant"
        self.ttl = get_settings().REDIS_CACHE_TTL

    def _key(self, plant_id: UUID) -> str:
        return f"{self.prefix}:{plant_id}"

    async def get_plant(self, plant_id: UUID) -> dict | None:
        try:
            data = await self.redis.get(self._key(plant_id))
            if data:
                logger.debug("cache_hit", plant_id=str(plant_id))
                return json.loads(data)
            logger.debug("cache_miss", plant_id=str(plant_id))
            return None
        except Exception as exc:
            logger.warning("cache_get_error", error=str(exc))
            return None

    async def set_plant(self, plant: object) -> None:
        try:
            plant_id = plant.id  # type: ignore[attr-defined]
            data = {
                "id": str(plant_id),
                "scientific_name": plant.scientific_name,  # type: ignore[attr-defined]
                "common_name": plant.common_name,  # type: ignore[attr-defined]
                "family": plant.family,  # type: ignore[attr-defined]
                "genus": plant.genus,  # type: ignore[attr-defined]
                "species": plant.species,  # type: ignore[attr-defined]
                "description": plant.description,  # type: ignore[attr-defined]
                "status": plant.status.value if plant.status else None,  # type: ignore[attr-defined]
            }
            await self.redis.set(
                self._key(plant_id), json.dumps(data), ex=self.ttl
            )
            logger.debug("cache_set", plant_id=str(plant_id))
        except Exception as exc:
            logger.warning("cache_set_error", error=str(exc))

    async def invalidate_plant(self, plant_id: UUID) -> None:
        try:
            await self.redis.delete(self._key(plant_id))
            logger.debug("cache_invalidated", plant_id=str(plant_id))
        except Exception as exc:
            logger.warning("cache_invalidate_error", error=str(exc))

    async def clear_all(self) -> None:
        try:
            keys = []
            async for key in self.redis.scan_iter(f"{self.prefix}:*"):
                keys.append(key)
            if keys:
                await self.redis.delete(*keys)
                logger.info("cache_cleared", count=len(keys))
        except Exception as exc:
            logger.warning("cache_clear_error", error=str(exc))
