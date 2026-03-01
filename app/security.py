from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet
import base64
import hashlib
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.jwt_expiration_minutes))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return int(user_id)


# Encryption for sensitive data (SSN/TIN, banking info)
def _get_fernet_key() -> bytes:
    """Generate Fernet key from settings encryption key"""
    key = hashlib.sha256(settings.encryption_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like SSN/TIN"""
    if not data:
        return ""
    fernet = Fernet(_get_fernet_key())
    return fernet.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return ""
    fernet = Fernet(_get_fernet_key())
    return fernet.decrypt(encrypted_data.encode()).decode()


def mask_ssn(ssn: str) -> str:
    """Mask SSN/TIN to show only last 4 digits"""
    if not ssn:
        return ""
    # Decrypt first if encrypted
    try:
        decrypted = decrypt_sensitive_data(ssn)
    except Exception:
        decrypted = ssn

    # Remove any non-digit characters
    digits = ''.join(c for c in decrypted if c.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***-**-{digits[-4:]}"
