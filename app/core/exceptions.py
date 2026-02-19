"""Custom exceptions and global exception handlers."""

from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger("exceptions")


class AuthServiceException(Exception):
    """Base exception for auth service."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize exception with message, code, and details."""
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationException(AuthServiceException):
    """Authentication-related exceptions."""
    pass


class AuthorizationException(AuthServiceException):
    """Authorization-related exceptions."""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Raised when user credentials are invalid."""
    pass


class ExpiredTokenException(AuthenticationException):
    """Raised when token has expired."""
    pass


class InvalidTokenException(AuthenticationException):
    """Raised when token is invalid or malformed."""
    pass


class UserNotFoundException(AuthServiceException):
    """Raised when user is not found."""
    pass


class UserAlreadyExistsException(AuthServiceException):
    """Raised when trying to create user that already exists."""
    pass


class UserInactiveException(AuthenticationException):
    """Raised when user account is inactive."""
    pass


class PasswordValidationException(AuthServiceException):
    """Raised when password doesn't meet requirements."""
    pass


class CircuitBreakerException(AuthServiceException):
    """Raised when circuit breaker is open."""
    pass


class DatabaseException(AuthServiceException):
    """Database-related exceptions."""
    pass


class RateLimitException(AuthServiceException):
    """Raised when rate limit is exceeded."""
    pass


class ValidationException(AuthServiceException):
    """Input validation exceptions."""
    pass


# Exception to HTTP status code mapping
EXCEPTION_STATUS_MAP = {
    InvalidCredentialsException: status.HTTP_401_UNAUTHORIZED,
    ExpiredTokenException: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenException: status.HTTP_401_UNAUTHORIZED,
    UserInactiveException: status.HTTP_401_UNAUTHORIZED,
    AuthenticationException: status.HTTP_401_UNAUTHORIZED,
    AuthorizationException: status.HTTP_403_FORBIDDEN,
    UserNotFoundException: status.HTTP_404_NOT_FOUND,
    UserAlreadyExistsException: status.HTTP_409_CONFLICT,
    PasswordValidationException: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ValidationException: status.HTTP_422_UNPROCESSABLE_ENTITY,
    RateLimitException: status.HTTP_429_TOO_MANY_REQUESTS,
    CircuitBreakerException: status.HTTP_503_SERVICE_UNAVAILABLE,
    DatabaseException: status.HTTP_503_SERVICE_UNAVAILABLE,
    AuthServiceException: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


async def auth_service_exception_handler(
    request: Request,
    exc: AuthServiceException
) -> JSONResponse:
    """Handle auth service custom exceptions."""
    status_code = EXCEPTION_STATUS_MAP.get(
        type(exc),
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    logger.warning(
        f"Auth service exception: {exc.message}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_code": exc.code,
            "exception_details": exc.details,
            "status_code": status_code,
            "path": str(request.url.path),
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "type": "auth_service_error"
            }
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation exceptions."""
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "path": str(request.url.path),
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {
                    "errors": exc.errors()
                },
                "type": "validation_error"
            }
        },
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database exceptions."""
    logger.error(
        "Database error",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "details": {},
                "type": "database_error"
            }
        },
    )


async def http_exception_custom_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
        }
    )

    # Use default handler for most cases but ensure consistent format
    response = await http_exception_handler(request, exc)

    # Convert to consistent error format if needed
    if hasattr(exc, 'detail') and isinstance(exc.detail, str):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {},
                    "type": "http_error"
                }
            },
        )

    return response


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
                "type": "internal_error"
            }
        },
    )