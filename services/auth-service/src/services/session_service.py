import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.session import UserSession

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
    ) -> UserSession:
        """Create a new user session."""
        user_session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(user_session)
        await self.session.flush()
        logger.info("session.created", user_id=str(user_id), session_id=str(user_session.id))
        return user_session

    async def get_session_by_token(self, refresh_token: str) -> UserSession | None:
        """Get a session by refresh token, only if not expired."""
        stmt = select(UserSession).where(
            UserSession.refresh_token == refresh_token,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
        """Get all active (non-expired) sessions for a user."""
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.now(timezone.utc),
        ).order_by(UserSession.created_at.desc())
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
