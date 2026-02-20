"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, Field, validator
from app.schemas.user import UserCreate


class LoginRequest(BaseModel):
    """Schema for user login requests."""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @validator('username')
    def validate_username(cls, v):
        """Normalize username for lookup."""
        return v.strip().lower()


class TokenResponse(BaseModel):
    """Schema for JWT token responses."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RegisterRequest(UserCreate):
    """Schema for user registration requests."""
    password_confirm: str = Field(..., min_length=8, max_length=128)

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str