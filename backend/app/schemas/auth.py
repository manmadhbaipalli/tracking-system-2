"""
Claims Service Platform - Authentication Schemas

Pydantic schemas for login, token response, and user role validation.
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime

from app.core.security import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores, and periods')
        return v.lower()


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_info: 'UserInfo'


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class UserInfo(BaseModel):
    """User information schema for token response"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime]
    permissions: List[str]

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        from app.utils.validators import validate_password_strength
        validate_password_strength(v)
        return v


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    """Reset password confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('new_password')
    def validate_password_strength(cls, v):
        from app.utils.validators import validate_password_strength
        validate_password_strength(v)
        return v


class UserCreate(BaseModel):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole = UserRole.VIEWER
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)

    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, underscores, and periods')
        return v.lower()

    @validator('password')
    def validate_password_strength(cls, v):
        from app.utils.validators import validate_password_strength
        validate_password_strength(v)
        return v

    @validator('phone')
    def validate_phone_format(cls, v):
        if v:
            from app.utils.validators import validate_phone
            validate_phone(v)
        return v

    class Config:
        use_enum_values = True


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr]
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[UserRole]
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool]
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)

    @validator('phone')
    def validate_phone_format(cls, v):
        if v:
            from app.utils.validators import validate_phone
            validate_phone(v)
        return v

    class Config:
        use_enum_values = True


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    status: str
    phone: Optional[str]
    department: Optional[str]
    title: Optional[str]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    timezone: str
    language: str
    created_at: datetime
    updated_at: datetime

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApiKeyCreate(BaseModel):
    """API key creation schema"""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ApiKeyResponse(BaseModel):
    """API key response schema"""
    id: int
    name: str
    key: str  # Only returned on creation
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PermissionCheck(BaseModel):
    """Permission check request schema"""
    permission: str
    resource_id: Optional[str]


class PermissionResponse(BaseModel):
    """Permission check response schema"""
    has_permission: bool
    user_role: UserRole
    required_permission: str

    class Config:
        use_enum_values = True


class SessionInfo(BaseModel):
    """Session information schema"""
    session_id: str
    user_id: int
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogoutRequest(BaseModel):
    """Logout request schema"""
    all_devices: bool = False


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str
    sessions_terminated: int


# Update forward references
TokenResponse.model_rebuild()