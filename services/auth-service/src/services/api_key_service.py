"""
API Key management service.
Keys are generated as `mpa_<random_32_bytes_hex>` (prefix + 64 hex chars).
Only the SHA-256 hash is stored; the plaintext is returned once at creation.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.api_key import APIKey

logger = structlog.get_logger()

_KEY_PREFIX = "mpa_"


def _generate_raw_key() -> str:
    """Generate a cryptographically random API key."""
    return _KEY_PREFIX + secrets.token_hex(32)  # 64 hex chars → 256 bits entropy


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of the raw key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _get_prefix(raw_key: str) -> str:
    """Return the first 12 characters for display (prefix + 8 chars)."""
    return raw_key[:12]


class APIKeyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(
        self,
        user_id: uuid.UUID,
        name: str,
        scopes: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.
        Returns (api_key_model, plaintext_key).
        The plaintext key is NOT stored and must be delivered to the user immediately.
        """
        raw_key = _generate_raw_key()
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_prefix=_get_prefix(raw_key),
            key_hash=_hash_key(raw_key),
            scopes=scopes or [],
            expires_at=expires_at,
        )
        self.session.add(api_key)
        await self.session.flush()
        logger.info("api_key.created", user_id=str(user_id), key_id=str(api_key.id), name=name)
        return api_key, raw_key

    async def validate_key(self, raw_key: str) -> APIKey | None:
        """
        Validate a raw API key string.
        Returns the APIKey model if valid and active, else None.
        Also updates last_used_at.
        """
        key_hash = _hash_key(raw_key)
        stmt = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
        result = await self.session.execute(stmt)
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return None

        # Check expiry
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            logger.info("api_key.expired", key_id=str(api_key.id))
            return None

        # Update last-used timestamp (best-effort)
        api_key.last_used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return api_key

    async def list_keys(self, user_id: uuid.UUID) -> list[APIKey]:
        """List all active API keys for a user."""
        stmt = select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke_key(self, key_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Revoke (deactivate) an API key."""
        stmt = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user_id)
        result = await self.session.execute(stmt)
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return False
        api_key.is_active = False
        await self.session.flush()
        logger.info("api_key.revoked", key_id=str(key_id), user_id=str(user_id))
        return True

    async def get_key(self, key_id: uuid.UUID, user_id: uuid.UUID) -> APIKey | None:
        stmt = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
