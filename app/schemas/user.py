"""Pydantic schemas for user registration, login, and responses."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (safe user data without password)."""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True