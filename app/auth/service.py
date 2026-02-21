"""Authentication business logic."""

from datetime import datetime, timedelta
import bcrypt
import jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.auth.models import User
from app.utils.exceptions import (
    ConflictError,
    AuthenticationError,
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID to encode in token

    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    expires = now + timedelta(minutes=settings.token_expiry_minutes)

    payload = {
        "user_id": user_id,
        "exp": expires,
        "iat": now,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


def verify_token(token: str) -> int:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID from token

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("user_id")
        if user_id is None:
            raise AuthenticationError("Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def register_user(
    email: str,
    password: str,
    db: Session,
) -> User:
    """Register a new user.

    Args:
        email: User email
        password: Plain text password
        db: Database session

    Returns:
        Created User model

    Raises:
        ConflictError: If email already exists
    """
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ConflictError("Email already registered")

    hashed_password = hash_password(password)
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(
    email: str,
    password: str,
    db: Session,
) -> User:
    """Login a user.

    Args:
        email: User email
        password: Plain text password
        db: Database session

    Returns:
        User model

    Raises:
        AuthenticationError: If credentials are invalid
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    return user
