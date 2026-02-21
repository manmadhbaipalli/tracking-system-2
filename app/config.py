"""Configuration management using Pydantic Settings"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration with environment variable support"""

    # Database configuration
    database_url: str = Field(
        default="sqlite:///./auth_service.db",
        description="Database connection URL"
    )

    # JWT configuration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="Secret key for JWT token signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=30,
        description="Refresh token expiration in days"
    )

    # Application configuration
    app_name: str = Field(
        default="FastAPI Auth Service",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # CORS configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    # Security configuration
    bcrypt_rounds: int = Field(
        default=12,
        description="Bcrypt hashing rounds"
    )

    # Circuit breaker configuration
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        description="Circuit breaker recovery timeout in seconds"
    )
    circuit_breaker_expected_exception: str = Field(
        default="Exception",
        description="Exception type that triggers circuit breaker"
    )

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()