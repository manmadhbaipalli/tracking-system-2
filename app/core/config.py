"""Application configuration management."""

from typing import Any, Dict, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Application"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "FastAPI application with authentication and circuit breaker"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 30
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: tuple = (Exception,)

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


# Global settings instance
settings = Settings()