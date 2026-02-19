from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    """User registration request schema."""

    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """User login request schema."""

    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    """User response schema for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response schema with user info."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str
    error_code: str
    timestamp: datetime
    request_id: str
