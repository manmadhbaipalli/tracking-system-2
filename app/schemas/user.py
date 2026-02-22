"""Pydantic schemas for user-related operations."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(UserBase):
    """Schema for user response data."""

    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    is_active: Optional[bool] = Field(None, description="Account active status")


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Schema for token payload data."""

    user_id: Optional[str] = None