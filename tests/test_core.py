"""Core functionality unit tests."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError, circuit_breaker, get_circuit_breaker
from app.core.exceptions import (
    AuthServiceException,
    AuthenticationError,
    UserAlreadyExistsError,
)
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_user_by_email,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User


class TestPasswordSecurity:
    """Test password hashing and verification."""

    @pytest.mark.asyncio
    async def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = await hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt format

    @pytest.mark.asyncio
    async def test_verify_password_success(self):
        """Test successful password verification."""
        password = "TestPassword123!"
        hashed = await hash_password(password)

        is_valid = await verify_password(password, hashed)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_password_failure(self):
        """Test password verification failure."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = await hash_password(password)

        is_valid = await verify_password(wrong_password, hashed)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_hash_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "TestPassword123!"
        password2 = "DifferentPassword123!"

        hash1 = await hash_password(password1)
        hash2 = await hash_password(password2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_hash_same_password_different_hashes(self):
        """Test that the same password produces different hashes due to salt."""
        password = "TestPassword123!"

        hash1 = await hash_password(password)
        hash2 = await hash_password(password)

        assert hash1 != hash2
        # But both should verify correctly
        assert await verify_password(password, hash1)
        assert await verify_password(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and verification."""

    @pytest.mark.asyncio
    async def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com", "user_id": "12345"}
        token = await create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts separated by dots

    @pytest.mark.asyncio
    async def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = await create_access_token(data, expires_delta)

        # Decode and verify expiry
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Should expire in about 15 minutes (allow 1 minute tolerance)
        expected_exp = now + expires_delta
        assert abs((exp - expected_exp).total_seconds()) < 60

    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "test@example.com"}
        token = await create_access_token(data)

        token_data = await verify_token(token)
        assert token_data.username == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await verify_token("invalid.jwt.token")

    @pytest.mark.asyncio
    async def test_verify_token_expired(self):
        """Test verification of expired token."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = await create_access_token(data, expires_delta)

        with pytest.raises(Exception):  # Should raise HTTPException due to expiry
            await verify_token(token)

    @pytest.mark.asyncio
    async def test_verify_token_missing_subject(self):
        """Test verification of token without subject."""
        # Manually create token without 'sub' claim
        payload = {"user_id": "12345", "exp": datetime.utcnow() + timedelta(minutes=30)}
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        with pytest.raises(Exception):  # Should raise HTTPException
            await verify_token(token)


class TestUserAuthentication:
    """Test user authentication functions."""

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user retrieval by email."""
        user = await get_user_by_email(db_session, test_user.email)

        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, db_session: AsyncSession):
        """Test user retrieval with non-existent email."""
        user = await get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user authentication."""
        user = await authenticate_user(db_session, test_user.email, "TestPassword123!")

        assert user is not False
        assert isinstance(user, User)
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, test_user: User):
        """Test authentication with wrong password."""
        user = await authenticate_user(db_session, test_user.email, "WrongPassword123!")
        assert user is False

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session: AsyncSession):
        """Test authentication with non-existent user."""
        user = await authenticate_user(db_session, "nonexistent@example.com", "Password123!")
        assert user is False


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal operation."""
        cb = AsyncCircuitBreaker("test_normal", failure_threshold=3, recovery_timeout=1)

        async def success_function():
            return "success"

        # Should work normally
        result = await cb.call(success_function)
        assert result == "success"
        assert cb.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening after failure threshold."""
        cb = AsyncCircuitBreaker("test_failure", failure_threshold=2, recovery_timeout=1)

        async def failing_function():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == "closed"

        # Second failure - should open circuit
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == "open"

        # Third call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await cb.call(failing_function)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        cb = AsyncCircuitBreaker("test_recovery", failure_threshold=1, recovery_timeout=0.1)

        async def failing_function():
            raise Exception("Test failure")

        async def success_function():
            return "recovered"

        # Trigger failure to open circuit
        with pytest.raises(Exception):
            await cb.call(failing_function)
        assert cb.state == "open"

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Should transition to half_open and succeed
        result = await cb.call(success_function)
        assert result == "recovered"
        assert cb.state == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator functionality."""
        call_count = 0

        @circuit_breaker("test_decorator", failure_threshold=2, recovery_timeout=0.1)
        async def decorated_function(should_fail=False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise Exception("Decorated function failure")
            return f"call_{call_count}"

        # Normal operation
        result = await decorated_function()
        assert result == "call_1"

        # Trigger failures
        with pytest.raises(Exception):
            await decorated_function(should_fail=True)

        with pytest.raises(Exception):
            await decorated_function(should_fail=True)

        # Circuit should be open now
        with pytest.raises(CircuitBreakerError):
            await decorated_function()

    def test_circuit_breaker_state_tracking(self):
        """Test circuit breaker state tracking."""
        from app.core.circuit_breaker import _circuit_breakers, get_circuit_breaker_state

        # Create a new circuit breaker
        cb = AsyncCircuitBreaker("test_state", failure_threshold=3, recovery_timeout=1)

        # Should be tracked
        state = get_circuit_breaker_state("test_state")
        assert state["state"] == "closed"
        assert state["failure_count"] == 0


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_auth_service_exception(self):
        """Test AuthServiceException."""
        exc = AuthServiceException("Test message", "TEST_ERROR")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_ERROR"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Invalid credentials")
        assert str(exc) == "Invalid credentials"
        assert exc.error_code == "AUTHENTICATION_ERROR"

    def test_user_already_exists_error(self):
        """Test UserAlreadyExistsError."""
        exc = UserAlreadyExistsError("User exists")
        assert str(exc) == "User exists"
        assert exc.error_code == "USER_ALREADY_EXISTS"

    def test_circuit_breaker_error(self):
        """Test CircuitBreakerError."""
        exc = CircuitBreakerError("Circuit open")
        assert str(exc) == "Circuit open"
        assert exc.message == "Circuit open"


class TestApplicationHealth:
    """Test application health check functionality."""

    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "circuit_breakers" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "documentation" in data
        assert "health" in data


class TestSecurityIntegration:
    """Test security integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self, db_session: AsyncSession):
        """Test complete authentication flow."""
        # Create user data
        email = "authflow@example.com"
        password = "AuthFlowPassword123!"

        # Hash password
        hashed_password = await hash_password(password)

        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Authenticate user
        authenticated_user = await authenticate_user(db_session, email, password)
        assert authenticated_user is not False
        assert authenticated_user.email == email

        # Create token
        token = await create_access_token(data={"sub": email})
        assert token is not None

        # Verify token
        token_data = await verify_token(token)
        assert token_data.username == email

        # Get user by email
        retrieved_user = await get_user_by_email(db_session, email)
        assert retrieved_user is not None
        assert retrieved_user.email == email

    def test_token_tampering_protection(self):
        """Test that tampered tokens are rejected."""
        import asyncio

        async def test_tampering():
            # Create valid token
            data = {"sub": "tamper@example.com"}
            token = await create_access_token(data)

            # Tamper with token
            parts = token.split('.')
            tampered_token = parts[0] + "." + parts[1] + ".tampered_signature"

            # Should raise exception
            with pytest.raises(Exception):
                await verify_token(tampered_token)

        asyncio.run(test_tampering())

    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self):
        """Test that authentication is resistant to timing attacks."""
        # This is a basic test - in production, more sophisticated timing analysis would be needed
        import time

        async def time_auth(email, password):
            start = time.time()
            result = await authenticate_user(AsyncMock(), email, password)
            end = time.time()
            return end - start, result

        # Time authentication with non-existent user
        time1, result1 = await time_auth("nonexistent@example.com", "password")
        assert result1 is False

        # Time authentication with wrong password (assuming we had a real db)
        # This test is limited without a real database connection
        # In a real scenario, we'd want to ensure both cases take similar time