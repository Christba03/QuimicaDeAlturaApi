import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.models.security_event import SecurityEventType
from src.models.verification_code import VerificationCodeType
from src.repositories.user_repository import UserRepository
from src.services.security_service import SecurityService
from src.services.verification_service import VerificationService

logger = structlog.get_logger()
router = APIRouter()


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


def get_verification_service(session: AsyncSession = Depends(get_db)) -> VerificationService:
    return VerificationService(session)


def get_security_service(session: AsyncSession = Depends(get_db)) -> SecurityService:
    return SecurityService(session)


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    payload: VerifyEmailRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    security_service: SecurityService = Depends(get_security_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Verify email address with verification code."""
    user = await user_repo.get_by_email(payload.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    # Verify the code
    if not await verification_service.verify_code(
        user.id, payload.code, VerificationCodeType.EMAIL_VERIFICATION
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Mark email as verified
    from datetime import datetime, timezone

    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    await user_repo.session.flush()

    # Log security event
    await security_service.log_security_event(
        SecurityEventType.EMAIL_VERIFIED,
        user_id=user.id,
    )

    logger.info("email.verified", user_id=str(user.id), email=payload.email)
    return {"message": "Email verified successfully"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    payload: ResendVerificationRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Resend email verification code."""
    user = await user_repo.get_by_email(payload.email)
    if user is None:
        # Don't reveal if user exists (security best practice)
        return {"message": "If the email exists, a verification code has been sent"}

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    # Send new verification code
    await verification_service.send_email_verification_code(user.id, user.email, user.first_name)

    logger.info("verification_code.resent", user_id=str(user.id), email=payload.email)
    return {"message": "If the email exists, a verification code has been sent"}
