from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="User password")
    full_name: str = Field(min_length=1, max_length=100, description="User full name")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, description="User password")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int