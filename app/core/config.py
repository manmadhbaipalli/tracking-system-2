"""Application configuration using Pydantic BaseSettings."""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, PostgresDsn, validator


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Server Configuration
    PROJECT_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI Authentication Service with Circuit Breaker"
    DEBUG: bool = False

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate and assemble CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[PostgresDsn] = None
    SQLITE_DATABASE_URL: str = "sqlite:///./auth_service.db"

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database URL from components."""
        if isinstance(v, str):
            return v

        # If PostgreSQL components are provided, use them
        if all([
            values.get("POSTGRES_SERVER"),
            values.get("POSTGRES_USER"),
            values.get("POSTGRES_PASSWORD"),
            values.get("POSTGRES_DB")
        ]):
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                user=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=values.get("POSTGRES_SERVER"),
                path=f"/{values.get('POSTGRES_DB') or ''}",
            )

        # Default to SQLite
        return values.get("SQLITE_DATABASE_URL")

    # Email Configuration (for future use)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Security Configuration
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds

    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "Exception"
    CIRCUIT_BREAKER_FALLBACK_FUNCTION: Optional[str] = None

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None

    # Redis Configuration (optional, for caching and distributed rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_PREFIX: str = "auth_service:"

    # Monitoring Configuration
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 5    # seconds

    # User Configuration
    USERS_OPEN_REGISTRATION: bool = True
    FIRST_SUPERUSER_EMAIL: Optional[EmailStr] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()