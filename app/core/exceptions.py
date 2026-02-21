"""Custom exception classes and global exception handlers."""
import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AuthServiceException(Exception):
    """Base exception for auth service."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        super().__init__(self.message)


class AuthenticationError(AuthServiceException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class UserExistsError(AuthServiceException):
    """User already exists."""

    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "USER_EXISTS_ERROR")


class UserNotFoundError(AuthServiceException):
    """User not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND_ERROR")


class InvalidTokenError(AuthServiceException):
    """Invalid token provided."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "INVALID_TOKEN_ERROR")


class ValidationError(AuthServiceException):
    """Validation error."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


async def auth_service_exception_handler(request: Request, exc: AuthServiceException) -> JSONResponse:
    """Handle AuthServiceException instances."""
    logger.error(f"Auth service error: {exc.message}", extra={"error_code": exc.error_code})

    # Map exception types to HTTP status codes
    status_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
        UserExistsError: status.HTTP_409_CONFLICT,
        UserNotFoundError: status.HTTP_404_NOT_FOUND,
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    }

    status_code = status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException instances."""
    logger.error(f"HTTP error: {exc.detail}", extra={"status_code": exc.status_code})

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error occurred")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )