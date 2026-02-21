"""
Claims Service Platform - Security Module

JWT token handling, password hashing, RBAC utilities, and security decorators.
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import hashlib
from enum import Enum

from app.core.config import settings
from app.core.database import get_db


class UserRole(str, Enum):
    """User role enumeration for RBAC"""
    ADMIN = "admin"
    ADJUSTER = "adjuster"
    PROCESSOR = "processor"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permission enumeration for fine-grained access control"""
    # Policy permissions
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    POLICY_SEARCH = "policy:search"

    # Claims permissions
    CLAIM_READ = "claim:read"
    CLAIM_WRITE = "claim:write"
    CLAIM_APPROVE = "claim:approve"
    CLAIM_CLOSE = "claim:close"

    # Payment permissions
    PAYMENT_READ = "payment:read"
    PAYMENT_CREATE = "payment:create"
    PAYMENT_APPROVE = "payment:approve"
    PAYMENT_PROCESS = "payment:process"
    PAYMENT_VOID = "payment:void"

    # Audit permissions
    AUDIT_READ = "audit:read"

    # User management permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"


# Role-to-permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # All permissions
        Permission.POLICY_READ, Permission.POLICY_WRITE, Permission.POLICY_SEARCH,
        Permission.CLAIM_READ, Permission.CLAIM_WRITE, Permission.CLAIM_APPROVE, Permission.CLAIM_CLOSE,
        Permission.PAYMENT_READ, Permission.PAYMENT_CREATE, Permission.PAYMENT_APPROVE,
        Permission.PAYMENT_PROCESS, Permission.PAYMENT_VOID,
        Permission.AUDIT_READ,
        Permission.USER_READ, Permission.USER_WRITE, Permission.USER_DELETE,
    ],
    UserRole.ADJUSTER: [
        Permission.POLICY_READ, Permission.POLICY_WRITE, Permission.POLICY_SEARCH,
        Permission.CLAIM_READ, Permission.CLAIM_WRITE, Permission.CLAIM_APPROVE,
        Permission.PAYMENT_READ, Permission.PAYMENT_CREATE,
        Permission.AUDIT_READ,
    ],
    UserRole.PROCESSOR: [
        Permission.POLICY_READ, Permission.POLICY_SEARCH,
        Permission.CLAIM_READ,
        Permission.PAYMENT_READ, Permission.PAYMENT_CREATE, Permission.PAYMENT_PROCESS,
        Permission.AUDIT_READ,
    ],
    UserRole.VIEWER: [
        Permission.POLICY_READ, Permission.POLICY_SEARCH,
        Permission.CLAIM_READ,
        Permission.PAYMENT_READ,
        Permission.AUDIT_READ,
    ],
}


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token

    Args:
        data: Token payload data
        expires_delta: Token expiration time (defaults to configured value)

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token

    Args:
        data: Token payload data

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token to verify

    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password

    Args:
        length: Password length (default: 12)

    Returns:
        str: Random password
    """
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data (SSN, credit card numbers, etc.)

    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end

    Returns:
        str: Masked data
    """
    if not data or len(data) <= visible_chars:
        return data

    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def mask_ssn(ssn: str) -> str:
    """
    Mask SSN with standard format (XXX-XX-1234)

    Args:
        ssn: Social Security Number

    Returns:
        str: Masked SSN
    """
    if not ssn:
        return ssn

    # Remove any existing formatting
    clean_ssn = ''.join(filter(str.isdigit, ssn))

    if len(clean_ssn) == 9:
        return f"XXX-XX-{clean_ssn[-4:]}"
    return mask_sensitive_data(ssn, visible_chars=4)


def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """
    Check if user role has required permission

    Args:
        user_role: User's role
        required_permission: Required permission

    Returns:
        bool: True if user has permission, False otherwise
    """
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])


def has_any_permission(user_role: UserRole, permissions: List[Permission]) -> bool:
    """
    Check if user role has any of the required permissions

    Args:
        user_role: User's role
        permissions: List of required permissions

    Returns:
        bool: True if user has any permission, False otherwise
    """
    user_permissions = ROLE_PERMISSIONS.get(user_role, [])
    return any(perm in user_permissions for perm in permissions)


async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Extract and verify current user token from request

    Args:
        credentials: HTTP authorization credentials

    Returns:
        dict: Decoded token payload

    Raises:
        HTTPException: If token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials.credentials:
        raise credentials_exception

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    return payload


def require_permission(required_permission: Permission):
    """
    Decorator to require specific permission for endpoint access

    Args:
        required_permission: Permission required to access the endpoint

    Returns:
        Function: FastAPI dependency function
    """
    async def permission_dependency(token: dict = Depends(get_current_user_token)):
        user_role = UserRole(token.get("role", ""))
        if not has_permission(user_role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return token

    return permission_dependency


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions for endpoint access

    Args:
        permissions: List of permissions, user needs any one

    Returns:
        Function: FastAPI dependency function
    """
    async def permission_dependency(token: dict = Depends(get_current_user_token)):
        user_role = UserRole(token.get("role", ""))
        if not has_any_permission(user_role, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return token

    return permission_dependency


def require_role(required_role: UserRole):
    """
    Decorator to require specific role for endpoint access

    Args:
        required_role: Role required to access the endpoint

    Returns:
        Function: FastAPI dependency function
    """
    async def role_dependency(token: dict = Depends(get_current_user_token)):
        user_role = UserRole(token.get("role", ""))
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.value} required"
            )
        return token

    return role_dependency


def create_api_key() -> str:
    """
    Generate a secure API key

    Returns:
        str: API key
    """
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage

    Args:
        api_key: API key to hash

    Returns:
        str: Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()