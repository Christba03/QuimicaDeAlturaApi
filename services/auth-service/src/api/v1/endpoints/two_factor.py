import uuid
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import get_db
from src.models.security_event import SecurityEventType
from src.repositories.user_repository import UserRepository
from src.config import settings
from src.services.security_service import SecurityService
from src.services.session_service import SessionService
from src.services.two_factor_service import TwoFactorService
from src.services.verification_service import VerificationService
from src.utils.security import create_access_token, create_refresh_token, decode_token

logger = structlog.get_logger()
router = APIRouter()


class Setup2FARequest(BaseModel):
    user_id: uuid.UUID


class Verify2FASetupRequest(BaseModel):
    user_id: uuid.UUID
    code: str = Field(..., min_length=6, max_length=6)


class Challenge2FARequest(BaseModel):
    challenge_token: str
    code: str = Field(..., min_length=6, max_length=8)  # TOTP is 6, backup codes are 8


class Request2FAEmailCodeRequest(BaseModel):
    challenge_token: str


class Disable2FARequest(BaseModel):
    user_id: uuid.UUID
    password: str


def get_two_factor_service(session: AsyncSession = Depends(get_db)) -> TwoFactorService:
    return TwoFactorService(session)


def get_verification_service(session: AsyncSession = Depends(get_db)) -> VerificationService:
    return VerificationService(session)


def get_security_service(session: AsyncSession = Depends(get_db)) -> SecurityService:
    return SecurityService(session)


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


@router.post("/setup", status_code=status.HTTP_200_OK)
async def setup_2fa(
    payload: Setup2FARequest,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Generate TOTP secret and QR code for 2FA setup."""
    user = await user_repo.get_by_id(payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled",
        )

    # Generate secret
    secret = two_factor_service.generate_totp_secret()
    uri = two_factor_service.get_totp_uri(user.email, secret)
    qr_code = two_factor_service.generate_qr_code(uri)

    # Store secret temporarily (user needs to verify before enabling)
    # In production, you might want to store this in Redis with expiration
    user.two_factor_secret = secret
    await user_repo.session.flush()

    logger.info("2fa.setup_initiated", user_id=str(user.id))
    return {
        "secret": secret,
        "qr_code": qr_code,
        "uri": uri,
    }


@router.post("/verify-setup", status_code=status.HTTP_200_OK)
async def verify_2fa_setup(
    payload: Verify2FASetupRequest,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    security_service: SecurityService = Depends(get_security_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Verify TOTP code and enable 2FA."""
    user = await user_repo.get_by_id(payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is already enabled",
        )

    if not user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Please call /setup first",
        )

    # Verify the code
    if not two_factor_service.verify_totp(user.two_factor_secret, payload.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    # Enable 2FA
    user.two_factor_enabled = True
    await user_repo.session.flush()

    # Generate backup codes
    backup_codes = two_factor_service.generate_backup_codes()
    await two_factor_service.create_backup_codes(user.id, backup_codes)

    # Log security event
    await security_service.log_security_event(
        SecurityEventType.TWO_FACTOR_ENABLED,
        user_id=user.id,
    )

    logger.info("2fa.enabled", user_id=str(user.id))
    return {
        "message": "Two-factor authentication enabled successfully",
        "backup_codes": backup_codes,  # Show only once!
    }


@router.post("/challenge", status_code=status.HTTP_200_OK)
async def challenge_2fa(
    payload: Challenge2FARequest,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    verification_service: VerificationService = Depends(get_verification_service),
    security_service: SecurityService = Depends(get_security_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Verify 2FA code during login and issue tokens."""
    # Decode challenge token to get user_id
    from src.utils.security import decode_token

    challenge_payload = decode_token(payload.challenge_token)
    if not challenge_payload or challenge_payload.get("type") != "2fa_challenge":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid challenge token",
        )

    user_id = uuid.UUID(challenge_payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active or not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")

    # Try different verification methods
    verified = False
    method = None

    # Try TOTP first (6 digits)
    if len(payload.code) == 6 and user.two_factor_secret:
        if two_factor_service.verify_totp(user.two_factor_secret, payload.code):
            verified = True
            method = "totp"
        else:
            # Try email code (also 6 digits)
            from src.models.verification_code import VerificationCodeType

            if await verification_service.verify_code(user.id, payload.code, VerificationCodeType.TWO_FACTOR_EMAIL):
                verified = True
                method = "email"
    # Try backup code (8 digits)
    elif len(payload.code) == 8:
        verified = await two_factor_service.verify_backup_code(user.id, payload.code)
        method = "backup_code" if verified else None

    if not verified:
        await security_service.log_security_event(
            SecurityEventType.TWO_FACTOR_FAILED,
            user_id=user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code",
        )

    # Log successful 2FA verification
    await security_service.log_security_event(
        SecurityEventType.TWO_FACTOR_VERIFIED,
        user_id=user.id,
        metadata={"method": method},
    )

    # Now issue tokens
    from datetime import datetime, timedelta, timezone

    session_service = SessionService(user_repo.session)
    role_names = [role.name for role in user.roles] if user.roles else []
    token_data = {"sub": str(user.id), "email": user.email, "roles": role_names}

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Generate device fingerprint for session
    from src.utils.device_fingerprint import generate_device_fingerprint, extract_device_name, detect_device_type
    
    device_fingerprint = generate_device_fingerprint(
        user_agent=challenge_payload.get("user_agent"),
        ip_address=challenge_payload.get("ip_address"),
    )
    device_name = extract_device_name(challenge_payload.get("user_agent"))
    device_type = detect_device_type(challenge_payload.get("user_agent"))
    
    await session_service.create_session(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=challenge_payload.get("ip_address"),
        user_agent=challenge_payload.get("user_agent"),
        accept_language=None,  # Not available in challenge payload
        device_fingerprint=device_fingerprint,
        device_name=device_name,
        device_type=device_type,
    )

    await security_service.handle_successful_login(user, challenge_payload.get("ip_address"))

    logger.info("2fa.verified", user_id=str(user.id), method=method)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/request-email-code", status_code=status.HTTP_200_OK)
async def request_2fa_email_code(
    payload: Request2FAEmailCodeRequest,
    verification_service: VerificationService = Depends(get_verification_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Request 2FA code via email."""
    challenge_payload = decode_token(payload.challenge_token)
    if not challenge_payload or challenge_payload.get("type") != "2fa_challenge":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid challenge token",
        )

    user_id = uuid.UUID(challenge_payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if user is None or not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid challenge")

    # Send email code
    from src.models.verification_code import VerificationCodeType

    await verification_service.send_two_factor_email_code(user.id, user.email, user.first_name)

    logger.info("2fa.email_code_sent", user_id=str(user.id))
    return {"message": "2FA code sent to your email"}


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    payload: Disable2FARequest,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    security_service: SecurityService = Depends(get_security_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Disable 2FA (requires password verification)."""
    user = await user_repo.get_by_id(payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )

    # Verify password
    from src.utils.security import verify_password

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    # Disable 2FA
    user.two_factor_enabled = False
    user.two_factor_secret = None
    await two_factor_service.delete_all_backup_codes(user.id)
    await user_repo.session.flush()

    # Log security event
    await security_service.log_security_event(
        SecurityEventType.TWO_FACTOR_DISABLED,
        user_id=user.id,
    )

    logger.info("2fa.disabled", user_id=str(user.id))
    return {"message": "Two-factor authentication disabled successfully"}


@router.get("/backup-codes", status_code=status.HTTP_200_OK)
async def get_backup_codes_count(
    user_id: uuid.UUID,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Get count of remaining backup codes."""
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )

    count = await two_factor_service.get_unused_backup_codes_count(user.id)
    return {"remaining_backup_codes": count}


@router.post("/regenerate-backup-codes", status_code=status.HTTP_200_OK)
async def regenerate_backup_codes(
    user_id: uuid.UUID,
    password: str,
    two_factor_service: TwoFactorService = Depends(get_two_factor_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Regenerate backup codes (requires password)."""
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not enabled",
        )

    # Verify password
    from src.utils.security import verify_password

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    # Delete old codes and generate new ones
    await two_factor_service.delete_all_backup_codes(user.id)
    backup_codes = two_factor_service.generate_backup_codes()
    await two_factor_service.create_backup_codes(user.id, backup_codes)

    logger.info("2fa.backup_codes_regenerated", user_id=str(user.id))
    return {
        "message": "Backup codes regenerated successfully",
        "backup_codes": backup_codes,  # Show only once!
    }
