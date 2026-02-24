import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.security import hash_password, verify_password, create_access_token
from app.exceptions import ConflictException, AuthException
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory rate limiting: email -> list of failed attempt timestamps
_failed_attempts: dict[str, list[datetime]] = {}


def _check_rate_limit(email: str) -> None:
    """Raise AuthException if the email has exceeded the failed login rate limit."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=settings.login_attempt_window_minutes)
    attempts = _failed_attempts.get(email, [])
    recent = [a for a in attempts if a > window_start]
    _failed_attempts[email] = recent
    if len(recent) >= settings.max_login_attempts:
        raise AuthException(
            f"Too many failed login attempts. Try again in {settings.login_attempt_window_minutes} minutes."
        )


def _record_failed_attempt(email: str) -> None:
    if email not in _failed_attempts:
        _failed_attempts[email] = []
    _failed_attempts[email].append(datetime.now(timezone.utc))


def _clear_failed_attempts(email: str) -> None:
    _failed_attempts.pop(email, None)


async def register_user(
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str,
) -> tuple[User, str]:
    """Register a new user and return (user, access_token)."""
    repo = UserRepository(session)

    if await repo.email_exists(email):
        raise ConflictException(f"Email {email} is already registered")

    password_hash = hash_password(password)
    user = await repo.create_user(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=UserRole.USER,
        active=True,
    )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    logger.info("User registered: user_id=%d", user.id)
    return user, token


async def login_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str]:
    """Authenticate a user and return (user, access_token)."""
    _check_rate_limit(email)

    repo = UserRepository(session)
    user = await repo.get_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        _record_failed_attempt(email)
        raise AuthException("Invalid email or password")

    if not user.active:
        raise AuthException("Account is disabled. Contact support.")

    _clear_failed_attempts(email)
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    logger.info("User logged in: user_id=%d", user.id)
    return user, token
