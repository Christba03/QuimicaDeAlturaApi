import base64
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from jose.backends import RSAKey
from passlib.context import CryptContext

from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT signing helpers — RS256 with HS256 fallback for local dev
# ---------------------------------------------------------------------------


def _get_sign_key() -> Any:
    """Return the private key (RS256) or shared secret (HS256 dev fallback)."""
    if settings.use_rsa:
        return settings.JWT_PRIVATE_KEY.replace("\\n", "\n")
    return settings.JWT_SECRET_KEY


def _get_verify_key() -> Any:
    """Return the public key (RS256) or shared secret (HS256 dev fallback)."""
    if settings.use_rsa:
        return settings.JWT_PUBLIC_KEY.replace("\\n", "\n")
    return settings.JWT_SECRET_KEY


def _algorithm() -> str:
    return "RS256" if settings.use_rsa else "HS256"


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token with a unique jti claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, _get_sign_key(), algorithm=_algorithm())


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT refresh token with a unique jti claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(timezone.utc),
    })
    return jwt.encode(to_encode, _get_sign_key(), algorithm=_algorithm())


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns the payload or None if invalid."""
    try:
        payload = jwt.decode(token, _get_verify_key(), algorithms=[_algorithm()])
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# JWKS (public key exposure for other services)
# ---------------------------------------------------------------------------


def get_jwks() -> dict:
    """
    Return a JWKS document with the active public key.
    Only meaningful when RS256 is configured; falls back to an empty keyset.
    """
    if not settings.use_rsa:
        return {"keys": []}

    pem = settings.JWT_PUBLIC_KEY.replace("\\n", "\n").encode()
    key = RSAKey(pem, algorithm="RS256")
    jwk = key.public_key().to_dict()

    # Ensure standard fields
    jwk.setdefault("use", "sig")
    jwk.setdefault("alg", "RS256")
    jwk.setdefault("kid", "auth-service-key-1")
    return {"keys": [jwk]}


# ---------------------------------------------------------------------------
# JWT blacklist (access tokens revoked before expiry)
# ---------------------------------------------------------------------------

_BLACKLIST_PREFIX = "jwt:blacklist:"


async def blacklist_token(redis_client, token_payload: dict) -> None:
    """
    Add a token's jti to the Redis blacklist with TTL = remaining lifetime.
    Call this on logout or explicit token revocation.
    """
    jti = token_payload.get("jti")
    exp = token_payload.get("exp")
    if not jti or not exp:
        return

    now = datetime.now(timezone.utc).timestamp()
    ttl = int(exp - now)
    if ttl > 0:
        await redis_client.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl, "1")


async def is_token_blacklisted(redis_client, token_payload: dict) -> bool:
    """Return True if the token has been explicitly revoked."""
    jti = token_payload.get("jti")
    if not jti:
        return False
    result = await redis_client.get(f"{_BLACKLIST_PREFIX}{jti}")
    return result is not None
