"""
Custom exceptions and global error handlers for the Claims System.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR
)
import logging

logger = logging.getLogger(__name__)


class ClaimSystemException(Exception):
    """Base exception for claims system."""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(ClaimSystemException):
    """Validation error exception."""
    pass


class NotFoundError(ClaimSystemException):
    """Resource not found exception."""
    pass


class AuthenticationError(ClaimSystemException):
    """Authentication error exception."""
    pass


class AuthorizationError(ClaimSystemException):
    """Authorization error exception."""
    pass


class BusinessLogicError(ClaimSystemException):
    """Business logic violation exception."""
    pass


class ExternalServiceError(ClaimSystemException):
    """External service integration error."""
    pass


class PaymentError(ClaimSystemException):
    """Payment processing error."""
    pass


# Global exception handlers
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.message}", extra={"error_code": exc.error_code})
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors."""
    logger.error(f"Not found error: {exc.message}", extra={"error_code": exc.error_code})
    return JSONResponse(
        status_code=HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle authentication errors."""
    logger.error(f"Authentication error: {exc.message}")
    return JSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content={
            "error": "Authentication Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle authorization errors."""
    logger.error(f"Authorization error: {exc.message}")
    return JSONResponse(
        status_code=HTTP_403_FORBIDDEN,
        content={
            "error": "Authorization Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )


async def business_logic_error_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handle business logic errors."""
    logger.error(f"Business logic error: {exc.message}", extra={"error_code": exc.error_code})
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Business Logic Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def payment_error_handler(request: Request, exc: PaymentError) -> JSONResponse:
    """Handle payment errors."""
    logger.error(f"Payment error: {exc.message}", extra={"error_code": exc.error_code})
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Payment Error",
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path
        }
    )


async def external_service_error_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    """Handle external service errors."""
    logger.error(f"External service error: {exc.message}", extra={"error_code": exc.error_code})
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "System is currently unavailable.",
            "message": "Please try again later.",
            "error_code": exc.error_code,
            "path": request.url.path
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": request.url.path
        }
    )


# Standardized error messages
ERROR_MESSAGES = {
    "NO_POLICIES_FOUND": "No matching policies found.",
    "NO_CLAIMS_FOUND": "No matching claims found.",
    "SYSTEM_UNAVAILABLE": "System is currently unavailable.",
    "UNABLE_TO_RETRIEVE": "Unable to retrieve details. Please try again later.",
    "UNABLE_TO_SAVE_CLAIM_POLICY": "Unable to save claim-level policy data. Please try again later.",
    "NO_PRIOR_CLAIMS": "No prior claims exist for this policy.",
    "INVALID_CREDENTIALS": "Invalid email or password.",
    "ACCESS_DENIED": "Access denied. Insufficient permissions.",
    "TOKEN_EXPIRED": "Access token has expired.",
    "TOKEN_INVALID": "Invalid access token.",
    "PAYMENT_PROCESSING_FAILED": "Payment processing failed. Please try again.",
    "EXTERNAL_SERVICE_UNAVAILABLE": "External service is currently unavailable.",
}


def get_error_message(error_code: str, default: str = "An error occurred.") -> str:
    """Get standardized error message by code."""
    return ERROR_MESSAGES.get(error_code, default)