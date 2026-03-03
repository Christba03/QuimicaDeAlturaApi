import structlog
from redis.asyncio import Redis
from typing import Optional

from src.config import settings

logger = structlog.get_logger()


class RateLimitService:
    """Service for Redis-based rate limiting."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self, identifier: str, limit: int, window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit for an identifier.
        
        Args:
            identifier: Unique identifier (IP address, email, etc.)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            tuple[bool, int, int]: (is_allowed, remaining, reset_after)
            - is_allowed: True if request is allowed
            - remaining: Number of requests remaining
            - reset_after: Seconds until limit resets
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, limit, window_seconds

        key = f"rate_limit:{identifier}"
        
        try:
            # Use Redis INCR with expiration for sliding window
            current = await self.redis.incr(key)
            
            if current == 1:
                # First request, set expiration
                await self.redis.expire(key, window_seconds)
            
            remaining = max(0, limit - current)
            is_allowed = current <= limit
            
            # Get TTL for reset_after
            ttl = await self.redis.ttl(key)
            reset_after = max(0, ttl) if ttl > 0 else window_seconds
            
            if not is_allowed:
                logger.warning(
                    "rate_limit.exceeded",
                    identifier=identifier,
                    current=current,
                    limit=limit,
                )
            
            return is_allowed, remaining, reset_after
            
        except Exception as e:
            logger.error("rate_limit.error", identifier=identifier, error=str(e))
            # On error, allow the request (fail open)
            return True, limit, window_seconds

    async def get_rate_limit_info(self, identifier: str) -> Optional[dict]:
        """Get current rate limit information for an identifier."""
        key = f"rate_limit:{identifier}"
        try:
            current = await self.redis.get(key)
            ttl = await self.redis.ttl(key)
            
            if current is None:
                return None
            
            return {
                "current": int(current),
                "ttl": ttl,
            }
        except Exception as e:
            logger.error("rate_limit.info_error", identifier=identifier, error=str(e))
            return None

    async def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for an identifier."""
        key = f"rate_limit:{identifier}"
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error("rate_limit.reset_error", identifier=identifier, error=str(e))
            return False
