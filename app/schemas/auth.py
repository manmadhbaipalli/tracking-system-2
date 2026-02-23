"""
Authentication request/response schemas with JWT token models and user registration.

Provides Pydantic models for:
- User login and authentication
- JWT token responses
- User registration and management
- Password reset and account management
"""

import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword"
            }
        }
    )


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: "UserResponse" = Field(..., description="User information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "role": "CLAIMS_ADJUSTER",
                    "is_active": True
                }
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="JWT refresh token")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class UserCreate(BaseModel):
    """User creation request schema."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "securepassword123",
                "first_name": "Jane",
                "last_name": "Smith",
                "role": "CLAIMS_ADJUSTER"
            }
        }
    )


class UserUpdate(BaseModel):
    """User update request schema."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "CLAIMS_ADJUSTER",
                "is_active": True,
                "last_login": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T09:00:00Z"
            }
        }
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr = Field(..., description="User email address")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = Field(default=True, description="Operation success status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[dict] = Field(None, description="Response data")


class APIError(BaseModel):
    """Standard API error response."""

    success: bool = Field(default=False, description="Operation success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "AUTHENTICATION_FAILED",
                "message": "Invalid email or password",
                "details": {
                    "field": "password",
                    "code": "INVALID_CREDENTIALS"
                }
            }
        }
    )


# Update forward references
TokenResponse.model_rebuild()