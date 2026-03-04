"""
OAuth 2.0 social login service.
Supports Google and GitHub via the authlib library.
"""
import secrets
import uuid

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.oauth_account import OAuthAccount
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.security import hash_password

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Provider configurations
# ---------------------------------------------------------------------------

PROVIDERS: dict[str, dict] = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scopes": "openid email profile",
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "emails_url": "https://api.github.com/user/emails",
        "scopes": "read:user user:email",
    },
}


class OAuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    def get_authorization_url(self, provider: str, state: str | None = None) -> str:
        """Build the OAuth authorization URL for the given provider."""
        cfg = PROVIDERS.get(provider)
        if not cfg:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        if provider == "google":
            client_id = settings.GOOGLE_CLIENT_ID
        elif provider == "github":
            client_id = settings.GITHUB_CLIENT_ID
        else:
            raise ValueError(f"Unsupported OAuth provider: {provider}")

        redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/{provider}/callback"
        state = state or secrets.token_urlsafe(32)

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": cfg["scopes"],
            "response_type": "code",
            "state": state,
        }
        if provider == "google":
            params["access_type"] = "online"

        from urllib.parse import urlencode
        return f"{cfg['auth_url']}?{urlencode(params)}", state

    async def exchange_code(self, provider: str, code: str) -> dict:
        """Exchange the authorization code for an access token."""
        cfg = PROVIDERS[provider]
        redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/oauth/{provider}/callback"

        if provider == "google":
            client_id = settings.GOOGLE_CLIENT_ID
            client_secret = settings.GOOGLE_CLIENT_SECRET
        else:
            client_id = settings.GITHUB_CLIENT_ID
            client_secret = settings.GITHUB_CLIENT_SECRET

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Accept": "application/json"}
            resp = await client.post(
                cfg["token_url"],
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_provider_user_info(self, provider: str, access_token: str) -> dict:
        """Fetch user profile from the provider using the access token."""
        cfg = PROVIDERS[provider]
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            resp = await client.get(cfg["userinfo_url"], headers=headers)
            resp.raise_for_status()
            data = resp.json()

            # GitHub: primary email may need a separate call
            if provider == "github" and not data.get("email"):
                emails_resp = await client.get(cfg["emails_url"], headers=headers)
                if emails_resp.status_code == 200:
                    for entry in emails_resp.json():
                        if entry.get("primary") and entry.get("verified"):
                            data["email"] = entry["email"]
                            break

            return data

    def _normalize_user_info(self, provider: str, raw: dict) -> dict:
        """Normalize provider-specific user info into a common format."""
        if provider == "google":
            return {
                "provider_user_id": raw["sub"],
                "email": raw.get("email"),
                "name": raw.get("name", ""),
                "avatar_url": raw.get("picture"),
                "raw": raw,
            }
        elif provider == "github":
            name = raw.get("name") or raw.get("login", "")
            parts = name.split(" ", 1)
            return {
                "provider_user_id": str(raw["id"]),
                "email": raw.get("email"),
                "name": name,
                "avatar_url": raw.get("avatar_url"),
                "raw": raw,
            }
        raise ValueError(f"Unknown provider: {provider}")

    async def authenticate_or_register(
        self, provider: str, code: str
    ) -> tuple[User, bool]:
        """
        Complete the OAuth flow: exchange code, fetch user info,
        then either log in an existing linked account or register a new user.
        Returns (user, is_new_user).
        """
        token_data = await self.exchange_code(provider, code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("OAuth provider did not return an access token")

        raw_info = await self.get_provider_user_info(provider, access_token)
        info = self._normalize_user_info(provider, raw_info)

        provider_user_id = info["provider_user_id"]
        email = info.get("email")

        # 1. Look up existing OAuth account linkage
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        result = await self.session.execute(stmt)
        oauth_account = result.scalar_one_or_none()

        if oauth_account:
            user = await self.user_repo.get_by_id(oauth_account.user_id)
            if user is None or not user.is_active:
                raise ValueError("Account is inactive")
            # Refresh provider data
            oauth_account.provider_data = info["raw"]
            oauth_account.provider_email = email
            oauth_account.provider_avatar_url = info.get("avatar_url")
            await self.session.flush()
            return user, False

        # 2. Try to link to existing user by email
        user = None
        is_new = False
        if email:
            user = await self.user_repo.get_by_email(email)

        # 3. Create new user
        if user is None:
            if not email:
                raise ValueError("OAuth provider did not return an email address")
            name_parts = info.get("name", "").split(" ", 1)
            user = User(
                email=email,
                hashed_password=hash_password(secrets.token_urlsafe(32)),  # unusable pw
                first_name=name_parts[0] if name_parts else "",
                last_name=name_parts[1] if len(name_parts) > 1 else "",
                email_verified=True,  # provider already verified
                is_active=True,
            )
            user = await self.user_repo.create(user)
            is_new = True

        # 4. Create the OAuth account linkage
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            provider_name=info.get("name"),
            provider_avatar_url=info.get("avatar_url"),
            provider_data=info["raw"],
        )
        self.session.add(oauth_account)
        await self.session.flush()

        logger.info(
            "oauth.authenticated",
            provider=provider,
            user_id=str(user.id),
            is_new=is_new,
        )
        return user, is_new
