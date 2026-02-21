"""
Claims Service Platform - Application Configuration

Environment-based configuration management using Pydantic settings.
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application settings
    APP_NAME: str = "Claims Service Platform"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/claims_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption settings
    ENCRYPTION_KEY: str = "your-32-char-encryption-key-here!!"
    FIELD_ENCRYPTION_SALT: str = "your-salt-for-field-encryption"

    # JWT settings
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External service configurations
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Payment processor settings
    ACH_PROVIDER_API_KEY: str = ""
    ACH_PROVIDER_URL: str = ""
    WIRE_PROVIDER_API_KEY: str = ""
    WIRE_PROVIDER_URL: str = ""

    # Audit settings
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years
    AUDIT_LOG_ARCHIVAL_ENABLED: bool = True

    # Search and pagination
    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 100
    SEARCH_TIMEOUT_SECONDS: int = 30

    # File upload settings
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".doc", ".docx", ".jpg", ".png", ".tiff"]
    UPLOAD_STORAGE_PATH: str = "uploads/"

    # Performance settings
    REQUEST_TIMEOUT_SECONDS: int = 30
    DATABASE_QUERY_TIMEOUT_SECONDS: int = 10

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Email settings (for notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    # Redis settings (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_EXPIRE_SECONDS: int = 3600

    # External integration settings
    XACTIMATE_API_URL: str = ""
    XACTIMATE_API_KEY: str = ""
    EDI_PROCESSING_ENDPOINT: str = ""
    ACCOUNTING_SYSTEM_API_URL: str = ""

    @validator("ENCRYPTION_KEY")
    def validate_encryption_key_length(cls, v):
        if len(v) != 32:
            raise ValueError("Encryption key must be exactly 32 characters long")
        return v

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


# Environment-specific configurations
def is_development() -> bool:
    """Check if running in development mode"""
    return settings.ENVIRONMENT.lower() == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return settings.ENVIRONMENT.lower() == "production"


def is_testing() -> bool:
    """Check if running in testing mode"""
    return settings.ENVIRONMENT.lower() == "testing"


# Database configuration helpers
def get_database_url() -> str:
    """Get database URL with fallback for testing"""
    if is_testing():
        return "postgresql://postgres:password@localhost:5432/claims_test_db"
    return settings.DATABASE_URL


# Security helpers
def get_password_hash_rounds() -> int:
    """Get bcrypt rounds based on environment"""
    return 4 if is_development() else 12