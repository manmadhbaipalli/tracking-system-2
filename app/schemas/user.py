"""
User management request/response schemas.

Handles all user-related data validation:
- User CRUD operations
- User profile management
- Role-based filtering
- User search and pagination
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from app.models.user import UserRole
from app.schemas.common import PaginationParams, PageResponse


class UserCreate(BaseModel):
    """User creation request schema (Admin only)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "AGENT"
            }
        }
    )

    email: EmailStr = Field(..., description="User email address (must be unique)")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password"
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User first name"
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User last name"
    )
    role: UserRole = Field(
        UserRole.VIEWER,
        description="User role (defaults to VIEWER)"
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format and normalize."""
        return v.lower().strip()

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """Validate and normalize names."""
        return v.strip().title()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for character variety
        has_lower = any(c.islower() for c in v)
        has_upper = any(c.isupper() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not all([has_lower, has_upper, has_digit, has_special]):
            raise ValueError(
                "Password must contain at least one lowercase letter, "
                "one uppercase letter, one digit, and one special character"
            )

        return v


class UserUpdate(BaseModel):
    """User update request schema."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "role": "ADJUSTER",
                "is_active": True
            }
        }
    )

    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User last name"
    )
    email: Optional[EmailStr] = Field(None, description="User email address")
    role: Optional[UserRole] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="User account status")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format and normalize."""
        return v.lower().strip() if v else v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize names."""
        return v.strip().title() if v else v


class UserProfileUpdate(BaseModel):
    """User profile update request schema (for current user)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com"
            }
        }
    )

    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User last name"
    )
    email: Optional[EmailStr] = Field(None, description="User email address")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format and normalize."""
        return v.lower().strip() if v else v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize names."""
        return v.strip().title() if v else v


class UserResponse(BaseModel):
    """User response schema for API responses."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "AGENT",
                "is_active": True,
                "is_locked": False,
                "failed_login_attempts": 0,
                "last_login": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T09:00:00Z"
            }
        }
    )

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name (computed)")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user account is active")
    is_locked: bool = Field(..., description="Whether user account is locked")
    failed_login_attempts: int = Field(..., description="Number of failed login attempts")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserListResponse(BaseModel):
    """User summary response for list endpoints."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "AGENT",
                "is_active": True,
                "last_login": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )

    id: UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name (computed)")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserSearchParams(PaginationParams):
    """User search and filtering parameters."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "search": "john",
                "role": "AGENT",
                "is_active": True,
                "page": 1,
                "size": 20
            }
        }
    )

    search: Optional[str] = Field(
        None,
        min_length=1,
        description="Search in name or email (case-insensitive)"
    )
    role: Optional[UserRole] = Field(None, description="Filter by user role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    created_after: Optional[datetime] = Field(
        None,
        description="Filter users created after this date"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filter users created before this date"
    )
    last_login_after: Optional[datetime] = Field(
        None,
        description="Filter users with last login after this date"
    )

    def validate_date_ranges(self) -> None:
        """Validate that date ranges are logical."""
        if (self.created_after and self.created_before and
                self.created_after > self.created_before):
            raise ValueError("created_after must be before created_before")


class UserStatsResponse(BaseModel):
    """User statistics response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_users": 150,
                "active_users": 140,
                "locked_users": 5,
                "users_by_role": {
                    "ADMIN": 3,
                    "AGENT": 45,
                    "ADJUSTER": 67,
                    "VIEWER": 35
                },
                "recent_registrations": 12,
                "recent_logins": 89
            }
        }
    )

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    locked_users: int = Field(..., description="Number of locked users")
    users_by_role: dict[UserRole, int] = Field(
        ...,
        description="User count by role"
    )
    recent_registrations: int = Field(
        ...,
        description="Number of users registered in last 30 days"
    )
    recent_logins: int = Field(
        ...,
        description="Number of users logged in within last 30 days"
    )


class UserAccountLockRequest(BaseModel):
    """Request to lock/unlock user account."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_locked": True,
                "reason": "Security investigation pending"
            }
        }
    )

    is_locked: bool = Field(..., description="Whether to lock the account")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for locking/unlocking the account"
    )


class UserRoleChangeRequest(BaseModel):
    """Request to change user role (Admin only)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "ADJUSTER",
                "reason": "Promotion to claims department"
            }
        }
    )

    role: UserRole = Field(..., description="New user role")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for role change"
    )


class BulkUserOperation(BaseModel):
    """Bulk operations on multiple users."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e8400-e29b-41d4-a716-446655440001"
                ],
                "operation": "deactivate",
                "reason": "Department restructuring"
            }
        }
    )

    user_ids: List[UUID] = Field(..., min_items=1, max_items=50)
    operation: str = Field(
        ...,
        regex="^(activate|deactivate|lock|unlock|delete)$",
        description="Operation to perform"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for bulk operation"
    )


class BulkOperationResult(BaseModel):
    """Result of bulk user operation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success_count": 8,
                "failure_count": 2,
                "total_count": 10,
                "failures": [
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "error": "User not found"
                    }
                ]
            }
        }
    )

    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    total_count: int = Field(..., description="Total number of operations attempted")
    failures: List[dict] = Field(
        default_factory=list,
        description="Details of failed operations"
    )


# Type aliases for common response patterns
UsersPageResponse = PageResponse[UserListResponse]
UserDetailResponse = UserResponse