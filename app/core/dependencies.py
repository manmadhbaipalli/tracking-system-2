from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.enums import Role
from app.repositories.user_repository import UserRepository
from app.exceptions import AuthException, ForbiddenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    subject = decode_access_token(token)
    if subject is None:
        raise AuthException("Invalid or expired token", "INVALID_TOKEN")

    try:
        user_id = int(subject)
    except (ValueError, TypeError):
        raise AuthException("Invalid token subject", "INVALID_TOKEN")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise AuthException("User not found", "USER_NOT_FOUND")

    if not user.active:
        raise ForbiddenException("Account is deactivated", "ACCOUNT_DEACTIVATED")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN:
        raise ForbiddenException("Admin access required", "INSUFFICIENT_PERMISSIONS")
    return current_user
