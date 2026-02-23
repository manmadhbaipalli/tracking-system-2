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

    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class IntegrationSettings(BaseModel):
    """External integration settings."""

    # Stripe Connect settings
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_connect_client_id: Optional[str] = None

    # Banking systems
    ach_api_key: Optional[str] = None
    ach_api_url: Optional[str] = None
    wire_transfer_api_key: Optional[str] = None
    wire_transfer_api_url: Optional[str] = None

    # Xactimate/XactAnalysis integration
    xactimate_api_key: Optional[str] = None
    xactimate_api_url: Optional[str] = None
    xactanalysis_api_key: Optional[str] = None
    xactanalysis_api_url: Optional[str] = None

    # EDI systems
    edi_835_endpoint: Optional[str] = None
    edi_837_endpoint: Optional[str] = None
    edi_api_key: Optional[str] = None

    # Document management
    document_storage_bucket: Optional[str] = None
    document_storage_key: Optional[str] = None
    document_storage_secret: Optional[str] = None

    # Bill review vendors
    bill_review_api_key: Optional[str] = None
    bill_review_api_url: Optional[str] = None

    # General ledger integration
    gl_api_key: Optional[str] = None
    gl_api_url: Optional[str] = None

    # Tax ID services
    tax_id_verification_api_key: Optional[str] = None
    tax_id_verification_api_url: Optional[str] = None

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_timeout: int = 60
    circuit_breaker_half_open_max_calls: int = 3

    # Retry settings
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 2.0
    retry_base_delay: float = 1.0


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
        description="JWT secret key for token signing - MUST be set via JWT_SECRET_KEY environment variable",
        min_length=32
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Integrations
    integrations: IntegrationSettings = IntegrationSettings()

    # Security
    encryption_key: Optional[str] = None
    password_min_length: int = 8
    max_failed_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 480  # 8 hours
    require_2fa: bool = False
    allowed_file_types: list[str] = ["pdf", "doc", "docx", "jpg", "jpeg", "png"]
    max_file_size_mb: int = 10

    # Performance
    max_search_results: int = 1000
    search_timeout_seconds: int = 3
    api_timeout_seconds: int = 5
    policy_search_cache_ttl: int = 300  # 5 minutes
    claim_details_cache_ttl: int = 60   # 1 minute
    max_concurrent_requests: int = 100
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    audit_log_retention_days: int = 2555  # 7 years
    enable_request_logging: bool = True
    log_sensitive_data: bool = False

    # Email settings
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: str = "noreply@insurance.com"

    # Monitoring and health checks
    enable_metrics: bool = True
    metrics_endpoint: str = "/metrics"
    health_check_endpoint: str = "/health"
    enable_database_health_check: bool = True

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