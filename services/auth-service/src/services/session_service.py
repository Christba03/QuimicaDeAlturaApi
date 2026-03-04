import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.session import UserSession
from src.utils.device_fingerprint import (
    detect_device_type,
    extract_device_name,
    generate_device_fingerprint,
)

logger = structlog.get_logger()


class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        user_id: uuid.UUID,
        refresh_token: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        accept_language: str | None = None,
        device_fingerprint: str | None = None,
        device_name: str | None = None,
        device_type: str | None = None,
        token_family: uuid.UUID | None = None,
        # GeoIP fields (resolved externally)
        country_code: str | None = None,
        country_name: str | None = None,
        region_name: str | None = None,
        city: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> UserSession:
        """Create a new user session with device fingerprinting and family tracking."""
        if not device_fingerprint:
            device_fingerprint = generate_device_fingerprint(
                user_agent=user_agent,
                ip_address=ip_address,
                accept_language=accept_language,
            )
        if not device_name:
            device_name = extract_device_name(user_agent)
        if not device_type:
            device_type = detect_device_type(user_agent)

        # Check if this device was previously trusted
        is_trusted = False
        trusted_until = None
        existing_trusted = await self.get_trusted_session_by_fingerprint(user_id, device_fingerprint)
        if existing_trusted:
            is_trusted = True
            trusted_until = datetime.now(timezone.utc) + timedelta(days=settings.TRUSTED_DEVICE_DURATION_DAYS)

        user_session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            device_name=device_name,
            device_type=device_type,
            token_family=token_family or uuid.uuid4(),
            family_invalidated=False,
            is_trusted=is_trusted,
            trusted_until=trusted_until,
            country_code=country_code,
            country_name=country_name,
            region_name=region_name,
            city=city,
            latitude=latitude,
            longitude=longitude,
        )
        self.session.add(user_session)
        await self.session.flush()
        logger.info(
            "session.created",
            user_id=str(user_id),
            session_id=str(user_session.id),
            device_fingerprint=device_fingerprint[:16] if device_fingerprint else None,
            is_trusted=is_trusted,
            token_family=str(user_session.token_family),
        )
        return user_session

    async def get_session_by_token(self, refresh_token: str) -> UserSession | None:
        """Get a session by refresh token, only if not expired and family is active."""
        stmt = select(UserSession).where(
            UserSession.refresh_token == refresh_token,
            UserSession.expires_at > datetime.now(timezone.utc),
            UserSession.family_invalidated == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_by_token_allow_invalidated(self, refresh_token: str) -> UserSession | None:
        """Get a session regardless of family invalidation status (for reuse detection)."""
        stmt = select(UserSession).where(UserSession.refresh_token == refresh_token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def invalidate_token_family(self, token_family: uuid.UUID) -> int:
        """Mark all sessions in a family as invalidated (reuse attack response)."""
        stmt = (
            update(UserSession)
            .where(UserSession.token_family == token_family)
            .values(family_invalidated=True)
        )
        result = await self.session.execute(stmt)
        count = result.rowcount
        logger.warning(
            "session.family_invalidated",
            token_family=str(token_family),
            sessions_affected=count,
        )
        return count

    async def revoke_session(self, refresh_token: str) -> bool:
        """Revoke a session by its refresh token."""
        stmt = delete(UserSession).where(UserSession.refresh_token == refresh_token)
        result = await self.session.execute(stmt)
        revoked = result.rowcount > 0
        if revoked:
            logger.info("session.revoked")
        return revoked

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Revoke all sessions for a user."""
        stmt = delete(UserSession).where(UserSession.user_id == user_id)
        result = await self.session.execute(stmt)
        count = result.rowcount
        logger.info("session.revoked_all", user_id=str(user_id), count=count)
        return count

    async def get_active_sessions(self, user_id: uuid.UUID) -> list[UserSession]:
        """Get all active (non-expired, non-invalidated) sessions for a user."""
        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.now(timezone.utc),
                UserSession.family_invalidated == False,
            )
            .order_by(UserSession.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_expired_sessions(self) -> int:
        """Delete all expired sessions."""
        stmt = delete(UserSession).where(UserSession.expires_at <= datetime.now(timezone.utc))
        result = await self.session.execute(stmt)
        count = result.rowcount
        if count > 0:
            logger.info("session.cleanup", expired_count=count)
        return count

    async def get_trusted_session_by_fingerprint(
        self, user_id: uuid.UUID, device_fingerprint: str
    ) -> UserSession | None:
        """Get a trusted session by device fingerprint."""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.device_fingerprint == device_fingerprint,
            UserSession.is_trusted == True,
            UserSession.trusted_until > datetime.now(timezone.utc),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_device_as_trusted(
        self, session_id: uuid.UUID, user_id: uuid.UUID, duration_days: int | None = None
    ) -> bool:
        """Mark a device as trusted."""
        stmt = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            return False

        duration = duration_days or settings.TRUSTED_DEVICE_DURATION_DAYS
        session.is_trusted = True
        session.trusted_until = datetime.now(timezone.utc) + timedelta(days=duration)

        await self.session.flush()
        logger.info("device.trusted", user_id=str(user_id), session_id=str(session_id))
        return True

    async def revoke_trusted_status(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Revoke trusted status from a device."""
        stmt = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            return False

        session.is_trusted = False
        session.trusted_until = None

        await self.session.flush()
        logger.info("device.trust_revoked", user_id=str(user_id), session_id=str(session_id))
        return True

    async def is_device_trusted(self, user_id: uuid.UUID, device_fingerprint: str) -> bool:
        """Check if a device is trusted."""
        trusted_session = await self.get_trusted_session_by_fingerprint(user_id, device_fingerprint)
        return trusted_session is not None
