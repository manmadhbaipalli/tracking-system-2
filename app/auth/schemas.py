"""Pydantic schemas for authentication."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str
