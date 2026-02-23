"""
Application configuration management using Pydantic Settings.

Environment-based configuration for:
- Database connections (SQLite dev, PostgreSQL prod)
- JWT authentication settings
- External integration credentials
- Logging and performance settings
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database configuration settings."""

    sqlite_url: str = "sqlite+aiosqlite:///./insurance.db"
    postgresql_url: Optional[str] = None
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class JWTSettings(BaseModel):
    """JWT authentication settings."""

    secret_key: str = Field(default="your-secret-key-change-in-production-must-be-at-least-32-chars-long!", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class IntegrationSettings(BaseModel):
    """External integration settings."""

    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    banking_api_key: Optional[str] = None
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_timeout: int = 60


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    app_name: str = "Insurance Management System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    database: DatabaseSettings = DatabaseSettings()

    # JWT - Direct fields for better env var integration
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production-must-be-at-least-32-chars-long!",
        min_length=32,
        description="JWT secret key for token signing"
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Integrations
    integrations: IntegrationSettings = IntegrationSettings()

    # Security
    encryption_key: Optional[str] = None
    password_min_length: int = 8

    # Performance
    max_search_results: int = 1000
    search_timeout_seconds: int = 3
    api_timeout_seconds: int = 5

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Get the appropriate database URL based on environment."""
        if self.environment == "production" and self.database.postgresql_url:
            return self.database.postgresql_url
        return self.database.sqlite_url

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def jwt(self) -> JWTSettings:
        """Get JWT settings as a JWTSettings object for backward compatibility."""
        return JWTSettings(
            secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.jwt_access_token_expire_minutes,
            refresh_token_expire_days=self.jwt_refresh_token_expire_days
        )


# Global settings instance
settings = Settings()