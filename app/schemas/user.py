"""Pydantic models for user data transfer objects."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user model with common fields."""

    email: EmailStr = Field(
        ..., description="User's email address", example="user@example.com"
    )

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class UserCreate(UserBase):
    """Model for creating a new user."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (8-100 characters)",
        example="SecurePassword123!",
    )

    @validator("password")
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
            }
        }


class UserUpdate(BaseModel):
    """Model for updating user information."""

    email: Optional[EmailStr] = Field(
        None, description="User's email address", example="user@example.com"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="User's password (8-100 characters)",
        example="NewSecurePassword123!",
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the user account is active", example=True
    )

    @validator("password")
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength requirements."""
        if v is None:
            return v

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "password": "NewSecurePassword123!",
                "is_active": True,
            }
        }


class UserResponse(UserBase):
    """Response model for user data (excludes sensitive information)."""

    id: UUID = Field(..., description="User's unique identifier")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }


class UserInDB(UserBase):
    """Model for user data as stored in database (includes sensitive fields)."""

    id: UUID
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True