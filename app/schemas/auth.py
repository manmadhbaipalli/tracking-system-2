"""Authentication-related Pydantic schemas"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Schema for user registration request"""

    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8-128 characters)",
        example="securepassword123"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one digit"
            )

        return v


class UserLogin(BaseModel):
    """Schema for user login request"""

    email: EmailStr = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        description="User password",
        example="securepassword123"
    )


class Token(BaseModel):
    """Schema for JWT token response"""

    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )


class TokenData(BaseModel):
    """Schema for JWT token payload data"""

    username: Optional[str] = Field(
        default=None,
        description="Username from token payload"
    )
    email: Optional[str] = Field(
        default=None,
        description="Email from token payload"
    )


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""

    refresh_token: str = Field(
        ...,
        description="Refresh token to exchange for new access token"
    )