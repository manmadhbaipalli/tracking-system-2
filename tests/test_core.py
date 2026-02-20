"""Tests for core functionality modules."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    authenticate_user,
)
from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    NotFoundException,
)
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


class TestSecurity:
    """Test security module functionality."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = hash_password(password)

        # Verify hash is different from original password
        assert hashed != password
        assert len(hashed) > 0
        # bcrypt hashes typically start with $2b$
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = hash_password(password)

        # Verify correct password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)

        # Verify incorrect password returns False
        assert verify_password(wrong_password, hashed) is False

    def test_create_access_token_default_expiry(self):
        """Test JWT token creation with default expiry."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify content
        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """Test JWT token creation with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)

        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"

        # Verify custom expiry is set (within reasonable range)
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_time = datetime.utcnow() + expires_delta
        # Allow 5 second variance for processing time
        assert abs((exp_time - expected_time).total_seconds()) < 5

    def test_decode_access_token_valid(self):
        """Test JWT token decoding with valid token."""
        data = {"sub": "testuser", "role": "user"}
        token = create_access_token(data)

        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_decode_access_token_invalid(self):
        """Test JWT token decoding with invalid token."""
        invalid_token = "invalid.jwt.token"

        with pytest.raises(JWTError):
            decode_access_token(invalid_token)

    def test_decode_access_token_expired(self):
        """Test JWT token decoding with expired token."""
        data = {"sub": "testuser"}
        # Create expired token
        expired_token = create_access_token(data, timedelta(seconds=-1))

        with pytest.raises(JWTError):
            decode_access_token(expired_token)

    @pytest.mark.asyncio
    async def test_authenticate_user_success_username(self, db_session: AsyncSession, test_user_data):
        """Test successful user authentication with username."""
        # Create user in database
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Authenticate with username
        authenticated_user = await authenticate_user(
            test_user_data["username"],
            test_user_data["password"],
            db_session
        )

        assert authenticated_user is not None
        assert authenticated_user.username == test_user_data["username"]
        assert authenticated_user.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_authenticate_user_success_email(self, db_session: AsyncSession, test_user_data):
        """Test successful user authentication with email."""
        # Create user in database
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Authenticate with email
        authenticated_user = await authenticate_user(
            test_user_data["email"],
            test_user_data["password"],
            db_session
        )

        assert authenticated_user is not None
        assert authenticated_user.username == test_user_data["username"]
        assert authenticated_user.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, test_user_data):
        """Test authentication with wrong password."""
        # Create user in database
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()

        # Try to authenticate with wrong password
        authenticated_user = await authenticate_user(
            test_user_data["username"],
            "WrongPassword123",
            db_session
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session: AsyncSession):
        """Test authentication with non-existent user."""
        authenticated_user = await authenticate_user(
            "nonexistent_user",
            "SomePassword123",
            db_session
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, db_session: AsyncSession, test_user_data):
        """Test authentication with inactive user."""
        # Create inactive user
        hashed_password = hash_password(test_user_data["password"])
        user = User(
            email=test_user_data["email"],
            username=test_user_data["username"],
            hashed_password=hashed_password,
            is_active=False  # Inactive user
        )
        db_session.add(user)
        await db_session.commit()

        # Try to authenticate inactive user
        authenticated_user = await authenticate_user(
            test_user_data["username"],
            test_user_data["password"],
            db_session
        )

        assert authenticated_user is None


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_authentication_exception(self):
        """Test AuthenticationException."""
        message = "Authentication failed"
        exc = AuthenticationException(message)

        assert str(exc) == message
        assert exc.status_code == 401
        assert exc.detail == message

    def test_conflict_exception(self):
        """Test ConflictException."""
        message = "Resource already exists"
        exc = ConflictException(message)

        assert str(exc) == message
        assert exc.status_code == 409
        assert exc.detail == message

    def test_not_found_exception(self):
        """Test NotFoundException."""
        message = "Resource not found"
        exc = NotFoundException(message)

        assert str(exc) == message
        assert exc.status_code == 404
        assert exc.detail == message


class TestLogging:
    """Test logging functionality."""

    def test_get_logger(self):
        """Test logger creation."""
        from app.core.logging import get_logger

        logger = get_logger("test.module")
        assert logger.name == "test.module"

    def test_set_correlation_id(self):
        """Test correlation ID generation."""
        from app.core.logging import set_correlation_id

        correlation_id = set_correlation_id()
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0

        # Test with custom correlation ID
        custom_id = "custom-id-123"
        result = set_correlation_id(custom_id)
        assert result == custom_id

    @patch('app.core.logging.logger')
    def test_log_request_info(self, mock_logger):
        """Test request logging."""
        from app.core.logging import log_request_info

        log_request_info(
            method="GET",
            url="http://test.com/api",
            headers={"User-Agent": "test"},
            correlation_id="test-123"
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Request received" in call_args[0][0]

    @patch('app.core.logging.logger')
    def test_log_response_info(self, mock_logger):
        """Test response logging."""
        from app.core.logging import log_response_info

        log_response_info(
            status_code=200,
            processing_time=0.5,
            correlation_id="test-123"
        )

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Request completed" in call_args[0][0]


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_decorator_success(self):
        """Test circuit breaker with successful function calls."""
        from app.core.circuit_breaker import with_circuit_breaker

        @with_circuit_breaker("test_operation")
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_circuit_breaker_decorator_failure(self):
        """Test circuit breaker with failing function calls."""
        from app.core.circuit_breaker import with_circuit_breaker

        @with_circuit_breaker("test_failing_operation")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_success(self):
        """Test async circuit breaker with successful calls."""
        from app.core.circuit_breaker import with_async_circuit_breaker

        @with_async_circuit_breaker("test_async_operation")
        async def successful_async_function():
            return "async success"

        result = await successful_async_function()
        assert result == "async success"

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_failure(self):
        """Test async circuit breaker with failing calls."""
        from app.core.circuit_breaker import with_async_circuit_breaker

        @with_async_circuit_breaker("test_async_failing_operation")
        async def failing_async_function():
            raise ValueError("Async test error")

        with pytest.raises(ValueError):
            await failing_async_function()


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-serve"
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Auth Serve"
        assert data["description"] == "A FastAPI-based authentication service"
        assert data["version"] == "1.0.0"
        assert data["docs_url"] == "/docs"
        assert data["health_url"] == "/health"