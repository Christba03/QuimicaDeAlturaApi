"""
OAuth 2.0 social login endpoints.
Supports Google and GitHub.

Flow:
  1. GET  /oauth/{provider}/authorize  → redirect URL + state (stored in session/cookie)
  2. GET  /oauth/{provider}/callback   → exchange code, issue JWT tokens
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.auth import TokenResponse
from src.services.auth_service import AuthService
from src.services.oauth_service import OAuthService, PROVIDERS
from src.services.webhook_service import webhook_service

logger = structlog.get_logger()
router = APIRouter()


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str
    provider: str


class OAuthVerifyTokenRequest(BaseModel):
    access_token: str


def get_oauth_service(session: AsyncSession = Depends(get_db)) -> OAuthService:
    return OAuthService(session)


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


@router.get("/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(
    provider: str,
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    """Return the OAuth provider authorization URL and state token."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")

    try:
        url, state = oauth_service.get_authorization_url(provider)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return OAuthAuthorizeResponse(authorization_url=url, state=state, provider=provider)


@router.get("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    request: Request,
    code: str = Query(..., description="Authorization code from provider"),
    state: str = Query(None, description="State token for CSRF protection"),
    oauth_service: OAuthService = Depends(get_oauth_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Handle OAuth provider callback: exchange code for tokens, return JWT.
    The `state` parameter should be validated against the value stored during authorize.
    """
    if provider not in PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    accept_language = request.headers.get("accept-language")

    try:
        user, is_new = await oauth_service.authenticate_or_register(provider, code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("oauth.callback_error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OAuth provider returned an error. Please try again.",
        )

    tokens = await auth_service.create_tokens(
        user,
        ip_address=ip_address,
        user_agent=user_agent,
        accept_language=accept_language,
    )

    await auth_service.security_service.handle_successful_login(user, ip_address)
    await webhook_service.emit("LOGIN_SUCCESS", user_id=str(user.id), data={"provider": provider})

    logger.info("oauth.login_complete", provider=provider, user_id=str(user.id), is_new=is_new)
    return tokens


@router.post("/{provider}/verify-token", response_model=TokenResponse)
async def oauth_verify_token(
    provider: str,
    request: Request,
    body: OAuthVerifyTokenRequest,
    oauth_service: OAuthService = Depends(get_oauth_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Handle native mobile OAuth login using an access token obtained directly 
    from the provider on the device (e.g., via Capacitor plugins).
    """
    if provider not in PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    accept_language = request.headers.get("accept-language")

    try:
        user, is_new = await oauth_service.authenticate_with_token(provider, body.access_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("oauth.verify_token_error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OAuth provider validation failed. Please try again.",
        )

    tokens = await auth_service.create_tokens(
        user,
        ip_address=ip_address,
        user_agent=user_agent,
        accept_language=accept_language,
    )

    await auth_service.security_service.handle_successful_login(user, ip_address)
    await webhook_service.emit("LOGIN_SUCCESS", user_id=str(user.id), data={"provider": provider, "method": "native_token"})

    logger.info("oauth.login_complete", provider=provider, user_id=str(user.id), is_new=is_new, method="native_token")
    return tokens
