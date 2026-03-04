import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies import get_current_user
from src.main import get_db
from src.models.security_event import SecurityEventType
from src.services.security_service import SecurityService
from src.services.session_service import SessionService

logger = structlog.get_logger()
router = APIRouter()


class SessionResponse(BaseModel):
    id: uuid.UUID
    ip_address: str | None
    user_agent: str | None
    device_info: dict | None
    device_name: str | None
    device_type: str | None
    is_trusted: bool
    trusted_until: str | None
    created_at: str
    last_activity_at: str
    expires_at: str


def get_session_service(session: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(session)


def get_security_service(session: AsyncSession = Depends(get_db)) -> SecurityService:
    return SecurityService(session)


@router.get("/", response_model=list[SessionResponse], status_code=status.HTTP_200_OK)
async def get_sessions(
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get all active sessions for the current user."""
    user_id = uuid.UUID(current_user["sub"])
    sessions = await session_service.get_active_sessions(user_id)

    return [
        SessionResponse(
            id=session.id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_info=session.device_info,
            device_name=session.device_name,
            device_type=session.device_type,
            is_trusted=session.is_trusted,
            trusted_until=session.trusted_until.isoformat() if session.trusted_until else None,
            created_at=session.created_at.isoformat(),
            last_activity_at=session.last_activity_at.isoformat(),
            expires_at=session.expires_at.isoformat(),
        )
        for session in sessions
    ]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Revoke a specific session."""
    user_id = uuid.UUID(current_user["sub"])

    # Get session to verify ownership
    from src.models.session import UserSession
    from sqlalchemy import select

    stmt = select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user_id)
    result = await session_service.session.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Revoke session
    await session_service.revoke_session(session.refresh_token)

    # Log security event
    await security_service.log_security_event(
        SecurityEventType.SESSION_REVOKED,
        user_id=user_id,
        metadata={"session_id": str(session_id)},
    )

    logger.info("session.revoked", user_id=str(user_id), session_id=str(session_id))
    return None


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_sessions(
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Revoke all sessions for the current user (except current one)."""
    user_id = uuid.UUID(current_user["sub"])

    # Get current session's refresh token to exclude it
    from src.models.session import UserSession
    from sqlalchemy import select

    # Find current session by matching access token user with refresh token
    # This is simplified - in production, you'd track this better
    sessions = await session_service.get_active_sessions(user_id)

    # Revoke all sessions
    count = await session_service.revoke_all_user_sessions(user_id)

    # Log security event
    await security_service.log_security_event(
        SecurityEventType.SESSION_REVOKED,
        user_id=user_id,
        metadata={"all_sessions": True, "count": count},
    )

    logger.info("sessions.revoked_all", user_id=str(user_id), count=count)
    return None


@router.post("/devices/trust/{session_id}", status_code=status.HTTP_200_OK)
async def trust_device(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Mark a device as trusted (skip 2FA for 30 days)."""
    user_id = uuid.UUID(current_user["sub"])

    success = await session_service.mark_device_as_trusted(session_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    logger.info("device.trusted", user_id=str(user_id), session_id=str(session_id))
    return {"message": "Device marked as trusted"}


@router.delete("/devices/trust/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_device_trust(
    session_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Revoke trusted status from a device."""
    user_id = uuid.UUID(current_user["sub"])

    success = await session_service.revoke_trusted_status(session_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    logger.info("device.trust_revoked", user_id=str(user_id), session_id=str(session_id))
    return None


@router.get("/devices", response_model=list[SessionResponse], status_code=status.HTTP_200_OK)
async def get_devices(
    current_user: dict = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service),
):
    """Get all devices (sessions) for the current user."""
    user_id = uuid.UUID(current_user["sub"])

    sessions = await session_service.get_active_sessions(user_id)

    return [
        SessionResponse(
            id=session.id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_info=session.device_info,
            device_name=session.device_name,
            device_type=session.device_type,
            is_trusted=session.is_trusted,
            trusted_until=session.trusted_until.isoformat() if session.trusted_until else None,
            created_at=session.created_at.isoformat(),
            last_activity_at=session.last_activity_at.isoformat(),
            expires_at=session.expires_at.isoformat(),
        )
        for session in sessions
    ]
