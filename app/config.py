"""Configuration management using Pydantic Settings."""

import os
from typing import Any, Dict, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="Auth-Serve", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Database
    database_url: str = Field(
        default="sqlite:///./auth_serve.db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=0, description="Database connection pool max overflow")

    # JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=60, description="JWT access token expiration in minutes"
    )

    # Security
    password_hash_rounds: int = Field(default=12, description="Password hash rounds")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="CORS allowed headers"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format (json or text)")

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(
        default=5, description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=30, description="Circuit breaker recovery timeout in seconds"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(
        default=100, description="Rate limit requests per minute"
    )

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()

    @validator("log_format")
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is either json or text."""
        if v.lower() not in ["json", "text"]:
            raise ValueError("Log format must be 'json' or 'text'")
        return v.lower()

    @validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v: str, values: dict) -> str:
        """Validate JWT secret key is not the default in production."""
        debug_mode = values.get("debug", False)
        # Only enforce strict validation if explicitly running in production
        # Check for common production environment indicators
        is_production = (
            os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") or
            os.getenv("NODE_ENV", "").lower() == "production" or
            (not debug_mode and os.getenv("JWT_SECRET_KEY") is not None)
        )

        if v == "your-secret-key-change-in-production" and is_production:
            raise ValueError("JWT secret key must be changed in production")
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with appropriate driver."""
        if self.database_url.startswith("sqlite"):
            if async_driver:
                return self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
            return self.database_url.replace("sqlite+aiosqlite://", "sqlite://")
        return self.database_url


# Global settings instance
settings = Settings()