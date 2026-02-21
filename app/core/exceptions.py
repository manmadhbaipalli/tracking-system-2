"""Custom exception classes and error handling"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AuthServiceException(Exception):
    """Base exception class for auth service"""

    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AuthServiceException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(AuthServiceException):
    """Authorization failed - insufficient permissions"""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationError(AuthServiceException):
    """Input validation failed"""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DatabaseError(AuthServiceException):
    """Database operation failed"""

    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class UserNotFoundError(AuthServiceException):
    """User not found"""

    def __init__(self, message: str = "User not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class UserAlreadyExistsError(AuthServiceException):
    """User already exists"""

    def __init__(self, message: str = "User already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class InactiveUserError(AuthServiceException):
    """User account is inactive"""

    def __init__(self, message: str = "User account is inactive", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


# Exception handlers
async def auth_service_exception_handler(request: Request, exc: AuthServiceException) -> JSONResponse:
    """
    Handler for custom auth service exceptions.

    Args:
        request: FastAPI request object
        exc: Auth service exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.error(
        f"Auth service exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
            }
        }
    )


async def validation_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for FastAPI validation exceptions.

    Args:
        request: FastAPI request object
        exc: HTTP exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.warning(
        f"Validation error: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": str(exc.detail),
                "status_code": exc.status_code,
                "path": request.url.path,
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: General exception

    Returns:
        JSONResponse: Structured error response
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "path": request.url.path,
            }
        }
    )