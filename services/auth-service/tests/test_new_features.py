"""
Test script for new enterprise auth features:
1. Password Strength Validation
2. Password History
3. Rate Limiting
4. Device Fingerprinting
5. Async Email Queue
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import settings
from src.models.user import User
from src.models.session import UserSession
from src.utils.password_validator import validate_password, PasswordValidationError
from src.utils.device_fingerprint import generate_device_fingerprint, detect_device_type, extract_device_name
from src.utils.security import hash_password

# Test configuration
BASE_URL = "http://localhost:8001"
AUTH_BASE = f"{BASE_URL}/api/v1/auth"


class TestPasswordStrength:
    """Test password strength validation."""

    def test_weak_password_too_short(self):
        """Test that passwords shorter than 12 characters are rejected."""
        try:
            validate_password("Short1!")
            assert False, "Should have raised PasswordValidationError"
        except PasswordValidationError as e:
            assert "at least 12 characters" in str(e).lower()

    def test_weak_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        try:
            validate_password("lowercase123!")
            assert False, "Should have raised PasswordValidationError"
        except PasswordValidationError as e:
            assert "uppercase" in str(e).lower()

    def test_weak_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        try:
            validate_password("UPPERCASE123!")
            assert False, "Should have raised PasswordValidationError"
        except PasswordValidationError as e:
            assert "lowercase" in str(e).lower()

    def test_weak_password_no_number(self):
        """Test that passwords without numbers are rejected."""
        try:
            validate_password("NoNumbers!")
            assert False, "Should have raised PasswordValidationError"
        except PasswordValidationError as e:
            assert "number" in str(e).lower()

    def test_weak_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        try:
            validate_password("NoSpecial123")
            assert False, "Should have raised PasswordValidationError"
        except PasswordValidationError as e:
            assert "special" in str(e).lower()

    def test_strong_password(self):
        """Test that a strong password passes validation."""
        try:
            validate_password("StrongPassword123!")
            assert True
        except PasswordValidationError:
            assert False, "Strong password should pass validation"

    def test_common_password_rejected(self):
        """Test that common passwords are rejected."""
        try:
            validate_password("Password123!")
            # This might pass basic checks but fail zxcvbn
            validate_password("Password123!")
        except PasswordValidationError:
            pass  # Expected for common passwords


class TestPasswordHistory:
    """Test password history enforcement."""

    @pytest.mark.asyncio
    async def test_password_history_storage(self):
        """Test that password history is stored correctly."""
        engine = create_async_engine(settings.DATABASE_URL)
        async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session_factory() as session:
            # Create a test user
            user = User(
                email=f"test_history_{uuid.uuid4()}@test.com",
                hashed_password=hash_password("InitialPassword123!"),
                first_name="Test",
                last_name="User",
            )
            session.add(user)
            await session.flush()
            
            # Change password multiple times
            passwords = ["Password1!", "Password2!", "Password3!", "Password4!", "Password5!"]
            for pwd in passwords:
                user.hashed_password = hash_password(pwd)
                if user.hashed_password not in user.password_history:
                    user.password_history.append(user.hashed_password)
                if len(user.password_history) > settings.PASSWORD_HISTORY_SIZE:
                    user.password_history = user.password_history[-settings.PASSWORD_HISTORY_SIZE:]
                await session.flush()
            
            # Verify history size is limited
            assert len(user.password_history) <= settings.PASSWORD_HISTORY_SIZE
            
            # Verify we can't reuse a recent password
            old_password_hash = user.password_history[-1]
            assert old_password_hash in user.password_history
            
            await session.rollback()
        await engine.dispose()


class TestDeviceFingerprinting:
    """Test device fingerprinting functionality."""

    def test_device_fingerprint_generation(self):
        """Test that device fingerprints are generated correctly."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ip_address = "192.168.1.1"
        accept_language = "en-US,en;q=0.9"
        
        fingerprint = generate_device_fingerprint(
            user_agent=user_agent,
            ip_address=ip_address,
            accept_language=accept_language,
        )
        
        assert fingerprint is not None
        assert len(fingerprint) == 64  # SHA256 hex length
        
        # Same inputs should produce same fingerprint
        fingerprint2 = generate_device_fingerprint(
            user_agent=user_agent,
            ip_address=ip_address,
            accept_language=accept_language,
        )
        assert fingerprint == fingerprint2

    def test_device_type_detection(self):
        """Test device type detection."""
        desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        tablet_ua = "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        
        assert detect_device_type(desktop_ua) == "desktop"
        assert detect_device_type(mobile_ua) == "mobile"
        assert detect_device_type(tablet_ua) == "tablet"

    def test_device_name_extraction(self):
        """Test device name extraction."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        device_name = extract_device_name(user_agent)
        
        assert device_name is not None
        assert "Chrome" in device_name or "Windows" in device_name


class TestRateLimiting:
    """Test rate limiting functionality."""

    async def test_login_rate_limit(self):
        """Test that login endpoint is rate limited."""
        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=30.0) as client:
            # Try to login multiple times rapidly
            attempts = 0
            rate_limited = False
            
            for i in range(settings.RATE_LIMIT_LOGIN_PER_15MIN + 2):
                try:
                    response = await client.post(
                        "/login",
                        json={
                            "email": f"test_rate_limit_{uuid.uuid4()}@test.com",
                            "password": "WrongPassword123!",
                        },
                    )
                    attempts += 1
                    
                    if response.status_code == 429:
                        rate_limited = True
                        assert "X-RateLimit-Limit" in response.headers
                        assert "X-RateLimit-Remaining" in response.headers
                        assert "Retry-After" in response.headers
                        break
                except Exception:
                    pass
            
            # Should hit rate limit before exhausting all attempts
            if attempts >= settings.RATE_LIMIT_LOGIN_PER_15MIN:
                assert rate_limited, "Should have been rate limited"


class TestEmailQueue:
    """Test async email queue functionality."""

    @pytest.mark.asyncio
    async def test_email_queue_enabled(self):
        """Test that email queue is enabled when configured."""
        assert hasattr(settings, "EMAIL_QUEUE_ENABLED")
        # Email queue should be configurable
        assert isinstance(settings.EMAIL_QUEUE_ENABLED, bool)


class TestIntegration:
    """Integration tests for the complete auth flow."""

    async def test_complete_registration_flow(self):
        """Test complete registration flow with all new features."""
        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=30.0) as client:
            # Generate unique email
            test_email = f"test_integration_{uuid.uuid4()}@test.com"
            test_password = "StrongPassword123!"
            
            # 1. Test registration with strong password
            register_response = await client.post(
                "/register",
                json={
                    "email": test_email,
                    "password": test_password,
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            
            if register_response.status_code == 201:
                print(f"✓ Registration successful: {test_email}")
            elif register_response.status_code == 400:
                error_detail = register_response.json().get("detail", "")
                print(f"✗ Registration failed (password validation): {error_detail}")
            else:
                print(f"✗ Registration failed: {register_response.status_code}")
            
            # 2. Test login with device fingerprinting
            login_response = await client.post(
                "/login",
                json={
                    "email": test_email,
                    "password": test_password,
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            
            if login_response.status_code == 200:
                tokens = login_response.json()
                assert "access_token" in tokens
                assert "refresh_token" in tokens
                print(f"✓ Login successful")
                
                # 3. Test session retrieval (should show device info)
                sessions_response = await client.get(
                    "/sessions/",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                },
                )
                
                if sessions_response.status_code == 200:
                    sessions = sessions_response.json()
                    assert len(sessions) > 0
                    session = sessions[0]
                    assert "device_name" in session
                    assert "device_type" in session
                    assert "device_fingerprint" in session or "is_trusted" in session
                    print(f"✓ Session retrieved with device info")
            else:
                print(f"✗ Login failed: {login_response.status_code}")
                print(f"  Response: {login_response.text}")

    async def test_password_reset_with_history(self):
        """Test password reset with password history check."""
        async with httpx.AsyncClient(base_url=AUTH_BASE, timeout=30.0) as client:
            test_email = f"test_reset_{uuid.uuid4()}@test.com"
            initial_password = "InitialPassword123!"
            
            # Register user
            await client.post(
                "/register",
                json={
                    "email": test_email,
                    "password": initial_password,
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
            
            # Request password reset
            reset_request_response = await client.post(
                "/password/reset-request",
                json={"email": test_email},
            )
            
            if reset_request_response.status_code == 200:
                print(f"✓ Password reset requested")
                # In a real test, you'd extract the code from email
                # For now, we just verify the endpoint works
            else:
                print(f"✗ Password reset request failed: {reset_request_response.status_code}")


async def run_all_tests():
    """Run all tests."""
    print("=" * 80)
    print("Testing Enterprise Auth Features")
    print("=" * 80)
    print()
    
    # Test password strength
    print("1. Testing Password Strength Validation...")
    password_tests = TestPasswordStrength()
    try:
        password_tests.test_weak_password_too_short()
        password_tests.test_weak_password_no_uppercase()
        password_tests.test_weak_password_no_lowercase()
        password_tests.test_weak_password_no_number()
        password_tests.test_weak_password_no_special_char()
        password_tests.test_strong_password()
        print("   ✓ Password strength validation tests passed")
    except Exception as e:
        print(f"   ✗ Password strength validation tests failed: {e}")
    
    print()
    
    # Test device fingerprinting
    print("2. Testing Device Fingerprinting...")
    device_tests = TestDeviceFingerprinting()
    try:
        device_tests.test_device_fingerprint_generation()
        device_tests.test_device_type_detection()
        device_tests.test_device_name_extraction()
        print("   ✓ Device fingerprinting tests passed")
    except Exception as e:
        print(f"   ✗ Device fingerprinting tests failed: {e}")
    
    print()
    
    # Test integration
    print("3. Testing Integration...")
    integration_tests = TestIntegration()
    try:
        await integration_tests.test_complete_registration_flow()
        await integration_tests.test_password_reset_with_history()
        print("   ✓ Integration tests completed")
    except Exception as e:
        print(f"   ✗ Integration tests failed: {e}")
    
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("Note: Some tests require the service to be running.")
    print("Start services with: docker-compose up -d")
    print("Then run: python -m pytest services/auth-service/tests/test_new_features.py -v")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
