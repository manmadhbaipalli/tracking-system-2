from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="User email address")
    password: str = Field(min_length=8, max_length=128, description="User password (min 8 characters)")
    name: str = Field(min_length=1, max_length=100, description="User display name")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "secret123",
                    "name": "Jane Doe",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token lifetime in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                }
            ]
        }
    }


class RegisterResponse(BaseModel):
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token lifetime in seconds")
    user: UserResponse = Field(description="Created user profile")
