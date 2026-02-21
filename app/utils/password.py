"""Password hashing and verification utilities"""
import bcrypt

from ..config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.

    Args:
        password: Plain text password to hash

    Returns:
        str: Bcrypt hashed password with salt
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password from database

    Returns:
        bool: True if password matches hash, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)