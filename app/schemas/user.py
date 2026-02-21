"""User-related Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""

    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    is_active: bool = Field(
        default=True,
        description="User account status"
    )


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        example="securepassword123"
    )


class UserResponse(UserBase):
    """Schema for user response data (excludes sensitive fields)"""

    id: int = Field(
        ...,
        description="User ID"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )

    class Config:
        """Pydantic configuration"""
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile"""

    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Account status"
    )

    class Config:
        """Pydantic configuration"""
        from_attributes = True