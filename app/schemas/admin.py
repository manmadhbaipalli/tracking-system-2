from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole


class AdminUpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    active: Optional[bool] = None


class AdminCreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)
    role: UserRole = UserRole.USER
