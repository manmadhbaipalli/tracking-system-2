"""Unit tests for exception classes."""

import pytest
from app.utils.exceptions import (
    AppException,
    AuthException,
    InvalidCredentialsException,
    UserAlreadyExistsException,
    TokenExpiredException,
    ValidationException,
    DatabaseException,
    CircuitBreakerOpenException,
    UserNotFoundException,
    UserInactiveException,
)


class TestExceptions:
    """Test exception classes."""

    def test_app_exception_base(self):
        """Test AppException base class."""
        exc = AppException("Test error", "TEST_ERROR", 400)
        assert exc.detail == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400

    def test_auth_exception(self):
        """Test AuthException."""
        exc = AuthException("Auth failed")
        assert exc.detail == "Auth failed"
        assert exc.error_code == "AUTH_ERROR"
        assert exc.status_code == 401

    def test_invalid_credentials_exception(self):
        """Test InvalidCredentialsException."""
        exc = InvalidCredentialsException()
        assert exc.error_code == "INVALID_CREDENTIALS"
        assert exc.status_code == 401

    def test_user_already_exists_exception_default(self):
        """Test UserAlreadyExistsException with default message."""
        exc = UserAlreadyExistsException()
        assert exc.error_code == "USER_ALREADY_EXISTS"
        assert exc.status_code == 409

    def test_user_already_exists_exception_with_field(self):
        """Test UserAlreadyExistsException with field name."""
        exc = UserAlreadyExistsException("email")
        assert "email" in exc.detail
        assert exc.error_code == "USER_ALREADY_EXISTS"
        assert exc.status_code == 409

    def test_token_expired_exception(self):
        """Test TokenExpiredException."""
        exc = TokenExpiredException()
        assert exc.error_code == "TOKEN_EXPIRED"
        assert exc.status_code == 401

    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid input")
        assert exc.detail == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_database_exception(self):
        """Test DatabaseException."""
        exc = DatabaseException()
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500

    def test_database_exception_custom_message(self):
        """Test DatabaseException with custom message."""
        exc = DatabaseException("Connection failed")
        assert exc.detail == "Connection failed"
        assert exc.error_code == "DATABASE_ERROR"

    def test_circuit_breaker_open_exception(self):
        """Test CircuitBreakerOpenException."""
        exc = CircuitBreakerOpenException()
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503

    def test_user_not_found_exception(self):
        """Test UserNotFoundException."""
        exc = UserNotFoundException()
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.status_code == 404

    def test_user_inactive_exception(self):
        """Test UserInactiveException."""
        exc = UserInactiveException()
        assert exc.error_code == "USER_INACTIVE"
        assert exc.status_code == 403

    def test_exception_is_exception_subclass(self):
        """Test that all custom exceptions are Exception subclasses."""
        assert issubclass(AppException, Exception)
        assert issubclass(AuthException, AppException)
        assert issubclass(InvalidCredentialsException, AuthException)
        assert issubclass(ValidationException, AppException)
