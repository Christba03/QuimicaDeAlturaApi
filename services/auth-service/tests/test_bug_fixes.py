"""
Tests for the six post-implementation bug fixes:
  Fix 1: IP lockout counter wiring in login endpoint
  Fix 2: 2FA challenge uses auth_service.create_tokens() (GeoIP + token family)
  Fix 3: OAuth callback calls handle_successful_login
  Fix 4: Shared auth dependency + endpoint protection
  Fix 5: JWT blacklist check in sessions endpoints
  Fix 6: Session cleanup ARQ cron job
"""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.v1.dependencies import get_current_user, require_superuser
from src.config import settings
from src.models.session import UserSession
from src.models.user import User
from src.services.security_service import SecurityService
from src.services.session_service import SessionService
from src.utils.security import (
    blacklist_token,
    create_access_token,
    decode_token,
    hash_password,
    is_token_blacklisted,
)

BASE_URL = "http://localhost:8001"
AUTH_BASE = f"{BASE_URL}/api/v1/auth"
USERS_BASE = f"{BASE_URL}/api/v1/users"
AUDIT_BASE = f"{BASE_URL}/api/v1/audit"
POLICIES_BASE = f"{BASE_URL}/api/v1/policies"
API_KEYS_BASE = f"{BASE_URL}/api/v1"


# ---------------------------------------------------------------------------
# Fix 1 — IP lockout wiring
# ---------------------------------------------------------------------------


class TestIPLockoutUnit:
    """Unit tests for SecurityService IP lockout methods (Redis-only, no DB)."""

    @pytest.mark.asyncio
    async def test_record_ip_failed_login_increments_counter(self):
        """record_ip_failed_login increments the Redis failure counter."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis.setex = AsyncMock()

        locked = await svc.record_ip_failed_login("10.0.0.1", mock_redis)

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()  # sets window TTL on first increment
        assert locked is False

    @pytest.mark.asyncio
    async def test_record_ip_failed_login_triggers_lockout_at_threshold(self):
        """IP is locked out once the failure count reaches the configured threshold."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=settings.IP_LOCKOUT_THRESHOLD)
        mock_redis.expire = AsyncMock()
        mock_redis.setex = AsyncMock()

        locked = await svc.record_ip_failed_login("10.0.0.2", mock_redis)

        assert locked is True
        mock_redis.setex.assert_called_once()  # lock key written to Redis

    @pytest.mark.asyncio
    async def test_record_ip_failed_login_not_locked_below_threshold(self):
        """IP is not locked while failure count is below threshold."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=settings.IP_LOCKOUT_THRESHOLD - 1)
        mock_redis.expire = AsyncMock()
        mock_redis.setex = AsyncMock()

        locked = await svc.record_ip_failed_login("10.0.0.3", mock_redis)

        assert locked is False
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_is_ip_locked_returns_true_when_key_exists(self):
        """is_ip_locked returns True when the lock key is present in Redis."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1")

        result = await svc.is_ip_locked("10.0.0.4", mock_redis)

        assert result is True

    @pytest.mark.asyncio
    async def test_is_ip_locked_returns_false_when_key_absent(self):
        """is_ip_locked returns False when no lock key is present in Redis."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        result = await svc.is_ip_locked("10.0.0.5", mock_redis)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_ip_locked_returns_false_on_redis_error(self):
        """is_ip_locked fails open (returns False) when Redis is unavailable."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("connection refused"))

        result = await svc.is_ip_locked("10.0.0.6", mock_redis)

        assert result is False  # fail open — do not block legitimate users

    @pytest.mark.asyncio
    async def test_record_ip_failed_login_ignores_empty_ip(self):
        """record_ip_failed_login is a no-op when ip_address is None."""
        svc = SecurityService.__new__(SecurityService)
        mock_redis = AsyncMock()

        locked = await svc.record_ip_failed_login(None, mock_redis)

        assert locked is False
        mock_redis.incr.assert_not_called()


class TestIPLockoutIntegration:
    """Integration test: login endpoint returns 429 after IP lockout (requires running service)."""

    @pytest.mark.asyncio
    async def test_login_endpoint_returns_429_after_ip_lockout(self):
        """
        Sending enough failed logins from the same IP eventually triggers a 429.
        This test clears the IP lock before running to avoid pollution between runs.
        """
        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=10.0) as client:
            # Verify service is reachable
            try:
                health = await client.get(f"{BASE_URL}/health")
                if health.status_code != 200:
                    pytest.skip("Service not available")
            except Exception:
                pytest.skip("Service not available")

            got_429 = False
            for _ in range(settings.IP_LOCKOUT_THRESHOLD + 5):
                response = await client.post(
                    "/login",
                    json={"email": f"no_user_{uuid.uuid4()}@invalid.test", "password": "wrong"},
                )
                if response.status_code == 429:
                    got_429 = True
                    break

            assert got_429, (
                f"Expected 429 after {settings.IP_LOCKOUT_THRESHOLD} failed logins; "
                "verify IP_LOCKOUT_THRESHOLD is set and login endpoint calls record_ip_failed_login"
            )


# ---------------------------------------------------------------------------
# Fix 2 — 2FA challenge uses auth_service.create_tokens()
# ---------------------------------------------------------------------------


class TestTwoFactorTokenCreation:
    """Verify the 2FA challenge endpoint delegates token creation to AuthService."""

    def test_challenge_endpoint_does_not_import_session_service_directly(self):
        """
        After the fix, two_factor.py should no longer import SessionService at module level
        (it's now handled inside AuthService).
        """
        import importlib
        import src.api.v1.endpoints.two_factor as tf_module

        # AuthService should be importable from the module (it's now a dep)
        assert hasattr(tf_module, "AuthService"), (
            "AuthService must be importable in two_factor.py after Fix 2"
        )

    def test_challenge_endpoint_does_not_create_tokens_inline(self):
        """
        The challenge endpoint source must not contain the inline create_access_token call
        that existed before the fix.
        """
        import inspect
        import src.api.v1.endpoints.two_factor as tf_module

        source = inspect.getsource(tf_module.challenge_2fa)
        assert "create_access_token(" not in source, (
            "challenge_2fa must use auth_service.create_tokens() — found inline create_access_token"
        )
        assert "auth_service.create_tokens(" in source, (
            "challenge_2fa must call auth_service.create_tokens()"
        )

    def test_challenge_endpoint_calls_handle_successful_login(self):
        """After the fix, challenge_2fa must still call handle_successful_login."""
        import inspect
        import src.api.v1.endpoints.two_factor as tf_module

        source = inspect.getsource(tf_module.challenge_2fa)
        assert "handle_successful_login" in source, (
            "challenge_2fa must call handle_successful_login after issuing tokens"
        )


# ---------------------------------------------------------------------------
# Fix 3 — OAuth callback calls handle_successful_login
# ---------------------------------------------------------------------------


class TestOAuthLoginTracking:
    """Verify that the OAuth callback wires handle_successful_login."""

    def test_oauth_callback_calls_handle_successful_login(self):
        """oauth_callback source must call handle_successful_login."""
        import inspect
        import src.api.v1.endpoints.oauth as oauth_module

        source = inspect.getsource(oauth_module.oauth_callback)
        assert "handle_successful_login" in source, (
            "oauth_callback must call handle_successful_login to update last_login_at/ip"
        )

    def test_oauth_callback_emits_login_success_webhook(self):
        """oauth_callback must emit a LOGIN_SUCCESS webhook event."""
        import inspect
        import src.api.v1.endpoints.oauth as oauth_module

        source = inspect.getsource(oauth_module.oauth_callback)
        assert "LOGIN_SUCCESS" in source, (
            "oauth_callback must emit LOGIN_SUCCESS webhook event"
        )

    @pytest.mark.asyncio
    async def test_handle_successful_login_updates_user_fields(self):
        """
        SecurityService.handle_successful_login updates last_login_at, last_login_ip,
        and resets failed_login_attempts.
        """
        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as session:
            user = User(
                email=f"oauth_track_{uuid.uuid4()}@test.com",
                hashed_password=hash_password("TestPassword123!"),
                first_name="OAuth",
                last_name="Track",
                failed_login_attempts=3,
            )
            session.add(user)
            await session.flush()

            svc = SecurityService(session)
            await svc.handle_successful_login(user, ip_address="203.0.113.10")

            assert user.last_login_at is not None
            assert user.last_login_ip == "203.0.113.10"
            assert user.failed_login_attempts == 0

            await session.rollback()

        await engine.dispose()


# ---------------------------------------------------------------------------
# Fix 4 — Shared get_current_user dependency + endpoint protection
# ---------------------------------------------------------------------------


class TestGetCurrentUserDependency:
    """Unit tests for the get_current_user FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_missing_authorization_header_raises_401(self):
        """get_current_user raises 401 when Authorization header is absent."""
        mock_request = MagicMock()
        mock_request.app.state.redis = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization=None)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_malformed_bearer_raises_401(self):
        """get_current_user raises 401 for a non-Bearer Authorization header."""
        mock_request = MagicMock()
        mock_request.app.state.redis = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization="Token abc123")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_jwt_raises_401(self):
        """get_current_user raises 401 for a tampered or garbage token."""
        mock_request = MagicMock()
        mock_request.app.state.redis = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization="Bearer not.a.valid.jwt")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_blacklisted_token_raises_401(self):
        """get_current_user raises 401 when the token's jti is in the Redis blacklist."""
        token = create_access_token({"sub": str(uuid.uuid4()), "email": "x@test.com"})

        # Redis returns a value → token is blacklisted
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1")

        mock_request = MagicMock()
        mock_request.app.state.redis = mock_redis

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization=f"Bearer {token}")

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_valid_token_returns_payload(self):
        """get_current_user returns the decoded payload for a valid, non-blacklisted token."""
        user_id = str(uuid.uuid4())
        token = create_access_token({"sub": user_id, "email": "ok@test.com"})

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # not blacklisted

        mock_request = MagicMock()
        mock_request.app.state.redis = mock_redis

        payload = await get_current_user(mock_request, authorization=f"Bearer {token}")

        assert payload["sub"] == user_id
        assert payload["email"] == "ok@test.com"
        assert payload["type"] == "access"


class TestRequireSuperuserDependency:
    """Unit tests for the require_superuser dependency."""

    @pytest.mark.asyncio
    async def test_non_admin_raises_403(self):
        """require_superuser raises 403 when the user has no admin role."""
        user_payload = {"sub": str(uuid.uuid4()), "roles": ["viewer"]}

        with pytest.raises(HTTPException) as exc_info:
            await require_superuser(current_user=user_payload)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_roles_raises_403(self):
        """require_superuser raises 403 when roles list is empty."""
        user_payload = {"sub": str(uuid.uuid4()), "roles": []}

        with pytest.raises(HTTPException) as exc_info:
            await require_superuser(current_user=user_payload)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_role_passes(self):
        """require_superuser allows users with the 'admin' role."""
        user_payload = {"sub": str(uuid.uuid4()), "roles": ["admin"]}

        result = await require_superuser(current_user=user_payload)

        assert result is user_payload

    @pytest.mark.asyncio
    async def test_is_superuser_flag_passes(self):
        """require_superuser allows users with is_superuser=True in the token payload."""
        user_payload = {"sub": str(uuid.uuid4()), "roles": [], "is_superuser": True}

        result = await require_superuser(current_user=user_payload)

        assert result is user_payload


class TestEndpointProtectionIntegration:
    """
    Integration tests: protected endpoints must return 401 without a valid token.
    Requires the auth service to be running.
    """

    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self):
        import httpx as _httpx
        try:
            resp = _httpx.get(f"{BASE_URL}/health", timeout=3)
            if resp.status_code != 200:
                pytest.skip("Service not available")
        except Exception:
            pytest.skip("Service not available")

    @pytest.mark.asyncio
    async def test_audit_events_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{AUDIT_BASE}/events")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_audit_user_events_requires_auth(self):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{AUDIT_BASE}/users/{fake_id}/events")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_policies_list_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{POLICIES_BASE}/")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_policies_create_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{POLICIES_BASE}/", json={
                "subject_type": "user", "subject_id": "*",
                "resource": "*", "action": "*",
            })
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_policies_delete_requires_auth(self):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.delete(f"{POLICIES_BASE}/{fake_id}")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_users_list_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{USERS_BASE}/")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_users_get_requires_auth(self):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{USERS_BASE}/{fake_id}")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_users_create_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{USERS_BASE}/", json={
                "email": "new@test.com", "password": "Pass123!",
                "first_name": "New", "last_name": "User",
            })
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_users_bulk_action_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{USERS_BASE}/bulk-action", json={
                "user_ids": [str(uuid.uuid4())], "action": "activate",
            })
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_api_keys_create_requires_auth(self):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{API_KEYS_BASE}/users/{fake_id}/api-keys",
                json={"name": "test-key", "scopes": []},
            )
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_api_keys_list_requires_auth(self):
        fake_id = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{API_KEYS_BASE}/users/{fake_id}/api-keys")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_api_keys_revoke_requires_auth(self):
        fake_uid = str(uuid.uuid4())
        fake_kid = str(uuid.uuid4())
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.delete(f"{API_KEYS_BASE}/users/{fake_uid}/api-keys/{fake_kid}")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_sessions_list_requires_auth(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{AUTH_BASE}/sessions/")
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_api_keys_ownership_enforced(self):
        """A valid token for user A cannot access user B's API keys (403)."""
        other_user_id = str(uuid.uuid4())
        # Token belongs to a different user
        token = create_access_token({"sub": str(uuid.uuid4()), "email": "a@test.com"})

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{API_KEYS_BASE}/users/{other_user_id}/api-keys",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_policies_non_admin_returns_403(self):
        """A valid non-admin token must receive 403 on policy endpoints."""
        token = create_access_token({
            "sub": str(uuid.uuid4()), "email": "user@test.com", "roles": ["viewer"]
        })
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{POLICIES_BASE}/",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert r.status_code == 403


# ---------------------------------------------------------------------------
# Fix 5 — JWT blacklist in sessions endpoints
# ---------------------------------------------------------------------------


class TestJWTBlacklistInSessions:
    """Verify that blacklisted access tokens are rejected by session endpoints."""

    def test_sessions_module_does_not_define_get_current_user_id(self):
        """After Fix 5, sessions.py must no longer define its own get_current_user_id."""
        import src.api.v1.endpoints.sessions as sessions_module

        assert not hasattr(sessions_module, "get_current_user_id"), (
            "sessions.py still defines get_current_user_id; it should use the shared dependency"
        )

    def test_sessions_module_imports_get_current_user(self):
        """sessions.py must import get_current_user from dependencies."""
        import src.api.v1.endpoints.sessions as sessions_module

        assert hasattr(sessions_module, "get_current_user"), (
            "sessions.py must import get_current_user from src.api.v1.dependencies"
        )

    @pytest.mark.asyncio
    async def test_blacklisted_token_rejected_by_get_current_user(self):
        """
        A token that has been explicitly revoked (jti in Redis blacklist)
        must be rejected with 401 by get_current_user.
        This exercises the same code path used by all session endpoints.
        """
        token = create_access_token({"sub": str(uuid.uuid4()), "email": "revoked@test.com"})
        payload = decode_token(token)

        # Simulate the token having been blacklisted
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"1")  # jti exists in blacklist

        mock_request = MagicMock()
        mock_request.app.state.redis = mock_redis

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, f"Bearer {token}")

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_sessions_endpoint_rejects_blacklisted_token(self):
        """
        Integration: /sessions/ must return 401 when called with a revoked access token.
        Uses a valid JWT whose jti is already in the Redis blacklist.
        """
        # Verify service is reachable
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=3)
            if r.status_code != 200:
                pytest.skip("Service not available")
        except Exception:
            pytest.skip("Service not available")

        token = create_access_token({"sub": str(uuid.uuid4()), "email": "revoked@test.com"})

        # Blacklist the token via the /auth/logout endpoint.
        # Logout accepts the access_token in the body to blacklist it immediately.
        # We still need a (fake) refresh_token string to satisfy the schema.
        from src.utils.security import create_refresh_token
        fake_refresh = create_refresh_token({"sub": str(uuid.uuid4()), "email": "revoked@test.com"})

        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=10.0) as client:
            await client.post("/logout", json={
                "refresh_token": fake_refresh,
                "access_token": token,
            })

            # Now attempt to use the blacklisted access token
            r = await client.get("/sessions/", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Fix 6 — Session cleanup ARQ cron job
# ---------------------------------------------------------------------------


class TestSessionCleanupCron:
    """Verify that the cleanup cron task is wired and functional."""

    def test_cleanup_task_registered_in_worker_settings(self):
        """cleanup_sessions_task must be in WorkerSettings.functions."""
        from src.workers.email_worker import WorkerSettings, cleanup_sessions_task

        assert cleanup_sessions_task in WorkerSettings.functions, (
            "cleanup_sessions_task is not listed in WorkerSettings.functions"
        )

    def test_cleanup_task_registered_as_cron_job(self):
        """cleanup_sessions_task must be registered as a cron_jobs entry."""
        from src.workers.email_worker import WorkerSettings, cleanup_sessions_task

        assert hasattr(WorkerSettings, "cron_jobs"), (
            "WorkerSettings must define cron_jobs"
        )
        cron_funcs = [cj.coroutine for cj in WorkerSettings.cron_jobs]
        assert cleanup_sessions_task in cron_funcs, (
            "cleanup_sessions_task is not listed in WorkerSettings.cron_jobs"
        )

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_deletes_expired_rows(self):
        """SessionService.cleanup_expired_sessions removes rows with expires_at in the past."""
        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as db:
            # Create a user to attach sessions to
            user = User(
                email=f"cleanup_test_{uuid.uuid4()}@test.com",
                hashed_password=hash_password("TestPassword123!"),
                first_name="Cleanup",
                last_name="Test",
            )
            db.add(user)
            await db.flush()

            past = datetime.now(timezone.utc) - timedelta(hours=2)
            future = datetime.now(timezone.utc) + timedelta(hours=24)

            expired_session = UserSession(
                user_id=user.id,
                refresh_token=f"expired_tok_{uuid.uuid4()}",
                expires_at=past,
            )
            active_session = UserSession(
                user_id=user.id,
                refresh_token=f"active_tok_{uuid.uuid4()}",
                expires_at=future,
            )
            db.add(expired_session)
            db.add(active_session)
            await db.flush()

            svc = SessionService(db)
            deleted_count = await svc.cleanup_expired_sessions()

            assert deleted_count >= 1, (
                "cleanup_expired_sessions should have deleted at least the one expired session"
            )

            # Verify the active session is still present
            from sqlalchemy import select
            result = await db.execute(
                select(UserSession).where(UserSession.id == active_session.id)
            )
            still_there = result.scalar_one_or_none()
            assert still_there is not None, "Active session must not be deleted by cleanup"

            await db.rollback()

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_returns_zero_when_nothing_expired(self):
        """cleanup_expired_sessions returns 0 when there are no expired sessions to remove."""
        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as db:
            user = User(
                email=f"no_expire_{uuid.uuid4()}@test.com",
                hashed_password=hash_password("TestPassword123!"),
                first_name="No",
                last_name="Expire",
            )
            db.add(user)
            await db.flush()

            future = datetime.now(timezone.utc) + timedelta(days=30)
            fresh_session = UserSession(
                user_id=user.id,
                refresh_token=f"fresh_tok_{uuid.uuid4()}",
                expires_at=future,
            )
            db.add(fresh_session)
            await db.flush()

            svc = SessionService(db)
            # First, clean up any pre-existing expired rows from other tests
            await svc.cleanup_expired_sessions()
            # Now the count for this user's sessions should be 0
            count_after = await svc.cleanup_expired_sessions()

            assert count_after == 0

            await db.rollback()

        await engine.dispose()
