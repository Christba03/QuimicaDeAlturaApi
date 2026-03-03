import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.models.security_event import SecurityEventType
from src.services.password_reset_service import PasswordResetService
from src.services.security_service import SecurityService
from src.utils.password_validator import PasswordValidationError

logger = structlog.get_logger()
router = APIRouter()


class PasswordResetRequestRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=12, max_length=128)


def get_password_reset_service(session: AsyncSession = Depends(get_db)) -> PasswordResetService:
    return PasswordResetService(session)


def get_security_service(session: AsyncSession = Depends(get_db)) -> SecurityService:
    return SecurityService(session)


@router.post("/reset-request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    payload: PasswordResetRequestRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Request a password reset code."""
    # Log the request
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(password_reset_service.session)
    user = await user_repo.get_by_email(payload.email)

    if user:
        await security_service.log_security_event(
            SecurityEventType.PASSWORD_RESET_REQUESTED,
            user_id=user.id,
        )

    # Send reset code (doesn't reveal if email exists)
    await password_reset_service.request_password_reset(payload.email)

    logger.info("password_reset.requested", email=payload.email)
    return {"message": "If the email exists, a password reset code has been sent"}


@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_password(
    payload: PasswordResetRequest,
    password_reset_service: PasswordResetService = Depends(get_password_reset_service),
    security_service: SecurityService = Depends(get_security_service),
):
    """Reset password using verification code."""
    try:
        success = await password_reset_service.reset_password(
            payload.email, payload.code, payload.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or verification code",
            )
    except PasswordValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Log the completion
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(password_reset_service.session)
    user = await user_repo.get_by_email(payload.email)

    if user:
        await security_service.log_security_event(
            SecurityEventType.PASSWORD_RESET_COMPLETED,
            user_id=user.id,
        )

    logger.info("password_reset.completed", email=payload.email)
    return {"message": "Password reset successfully"}
