"""Custom exceptions and global exception handlers for FastAPI."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthenticationError(HTTPException):
    """Exception raised for authentication failures."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Exception raised for authorization failures."""

    def __init__(self, detail: str = "Not authorized to access this resource") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(HTTPException):
    """Exception raised for validation errors."""

    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotFoundError(HTTPException):
    """Exception raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """Exception raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, detail: str = "Resource conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class CircuitBreakerError(HTTPException):
    """Exception raised when circuit breaker is open."""

    def __init__(self, detail: str = "Service temporarily unavailable") -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail
        )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions.

    Args:
        request: The FastAPI request object
        exc: The unhandled exception

    Returns:
        JSON response with error details
    """
    logger.error(
        "Unhandled exception occurred",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions.

    Args:
        request: The FastAPI request object
        exc: The HTTP exception

    Returns:
        JSON response with error details
    """
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Map status codes to error codes
    error_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        503: "SERVICE_UNAVAILABLE",
    }

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": error_code_mapping.get(exc.status_code, "HTTP_ERROR"),
        },
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handler for validation exceptions from Pydantic.

    Args:
        request: The FastAPI request object
        exc: The validation exception

    Returns:
        JSON response with validation error details
    """
    logger.warning(
        "Validation exception occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": getattr(exc, "errors", None),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": getattr(exc, "errors", []),
        },
    )