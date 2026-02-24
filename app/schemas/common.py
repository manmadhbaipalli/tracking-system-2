"""
Common response schemas and pagination models.

Provides shared response structures used across all API endpoints:
- Error responses with correlation IDs
- Paginated response envelopes
- Health check responses
- Base response classes
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Generic type for paginated items
T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Detailed error information for validation failures."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "code": "INVALID_FORMAT"
            }
        }
    )

    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """Standard error response format with correlation ID for tracing."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [
                        {
                            "field": "email",
                            "message": "Invalid email format",
                            "code": "INVALID_FORMAT"
                        }
                    ],
                    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    )

    error: "ErrorInfo"


class ErrorInfo(BaseModel):
    """Error information container."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = Field(
        None,
        description="Additional error details"
    )
    correlation_id: UUID = Field(..., description="Request correlation ID for tracing")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error occurrence timestamp"
    )


class PageResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "page": 1,
                "size": 20,
                "total": 150,
                "pages": 8,
                "has_next": True,
                "has_prev": False
            }
        }
    )

    items: List[T] = Field(..., description="List of items for current page")
    page: int = Field(..., ge=1, description="Current page number (1-based)")
    size: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def create(
        cls,
        items: List[T],
        page: int,
        size: int,
        total: int
    ) -> "PageResponse[T]":
        """
        Create a paginated response.

        Args:
            items: Items for current page
            page: Current page number
            size: Items per page
            total: Total number of items

        Returns:
            Paginated response instance
        """
        pages = (total + size - 1) // size if total > 0 else 0

        return cls(
            items=items,
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class HealthCheck(BaseModel):
    """Health check response for monitoring endpoints."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0"
            }
        }
    )

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    version: str = Field(..., description="Application version")


class ReadinessCheck(HealthCheck):
    """Extended health check with dependency status."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                "checks": {
                    "database": "healthy",
                    "redis": "healthy",
                    "external_services": "healthy"
                }
            }
        }
    )

    checks: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of individual system dependencies"
    )


class SuccessResponse(BaseModel):
    """Generic success response for operations without data."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )

    success: bool = Field(True, description="Operation success indicator")
    message: str = Field(..., description="Success message")
    correlation_id: UUID = Field(..., description="Request correlation ID")


class IdResponse(BaseModel):
    """Response containing created resource ID."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Resource created successfully"
            }
        }
    )

    id: UUID = Field(..., description="Created resource ID")
    message: str = Field("Resource created successfully", description="Success message")


# Common query parameters for searching and pagination
class PaginationParams(BaseModel):
    """Common pagination query parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")


class DateRangeParams(BaseModel):
    """Common date range query parameters."""

    date_from: Optional[datetime] = Field(None, description="Start date for range filter")
    date_to: Optional[datetime] = Field(None, description="End date for range filter")

    def validate_range(self) -> None:
        """Validate that date_from <= date_to if both are provided."""
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be less than or equal to date_to")


class SortParams(BaseModel):
    """Common sorting parameters."""

    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field(
        "asc",
        regex="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'"
    )


# Response status constants
class ResponseStatus:
    """Common response status constants."""

    SUCCESS = "success"
    ERROR = "error"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    READY = "ready"
    NOT_READY = "not_ready"


# Common error codes
class ErrorCodes:
    """Standard error code constants."""

    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_INSUFFICIENT_PRIVILEGES = "AUTH_INSUFFICIENT_PRIVILEGES"
    AUTH_ACCOUNT_LOCKED = "AUTH_ACCOUNT_LOCKED"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    VALIDATION_REQUIRED_FIELD = "VALIDATION_REQUIRED_FIELD"
    VALIDATION_INVALID_FORMAT = "VALIDATION_INVALID_FORMAT"
    VALIDATION_VALUE_OUT_OF_RANGE = "VALIDATION_VALUE_OUT_OF_RANGE"

    # Business logic errors
    POLICY_NOT_FOUND = "POLICY_NOT_FOUND"
    POLICY_EXPIRED = "POLICY_EXPIRED"
    CLAIM_NOT_FOUND = "CLAIM_NOT_FOUND"
    CLAIM_STATUS_INVALID = "CLAIM_STATUS_INVALID"
    PAYMENT_INSUFFICIENT_RESERVES = "PAYMENT_INSUFFICIENT_RESERVES"
    PAYMENT_ALREADY_PROCESSED = "PAYMENT_ALREADY_PROCESSED"

    # System errors
    SYSTEM_UNAVAILABLE = "SYSTEM_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# Common error messages
class ErrorMessages:
    """Standard error message constants."""

    # Authentication messages
    INVALID_CREDENTIALS = "Invalid email or password"
    TOKEN_EXPIRED = "Access token has expired"
    TOKEN_INVALID = "Invalid or malformed token"
    INSUFFICIENT_PRIVILEGES = "Insufficient privileges for this operation"
    ACCOUNT_LOCKED = "Account is temporarily locked due to failed login attempts"

    # Validation messages
    REQUIRED_FIELD = "Required field is missing: {field}"
    INVALID_FORMAT = "Invalid format for field: {field}"
    VALUE_OUT_OF_RANGE = "Value out of acceptable range for field: {field}"

    # Business logic messages
    POLICY_NOT_FOUND = "Policy not found"
    POLICY_EXPIRED = "Policy has expired"
    CLAIM_NOT_FOUND = "Claim not found"
    CLAIM_STATUS_INVALID = "Invalid status transition"
    PAYMENT_INSUFFICIENT_RESERVES = "Insufficient reserves for payment amount"
    PAYMENT_ALREADY_PROCESSED = "Payment has already been processed"

    # System messages
    SYSTEM_UNAVAILABLE = "System is currently unavailable"
    DATABASE_ERROR = "Database operation failed"
    EXTERNAL_SERVICE_ERROR = "External service integration failed"
    RATE_LIMIT_EXCEEDED = "API rate limit exceeded"
    NO_MATCHING_RESULTS = "No matching {resource} found"
    UNABLE_TO_RETRIEVE = "Unable to retrieve {resource}. Please try again later"