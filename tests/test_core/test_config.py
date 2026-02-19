"""Tests for app.core.config module."""

import os
import tempfile
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Test Settings class configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        # API Configuration
        assert settings.API_V1_STR == "/api/v1"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30
        assert settings.ALGORITHM == "HS256"
        assert len(settings.SECRET_KEY) > 0  # Should generate a random key

        # Server Configuration
        assert settings.PROJECT_NAME == "Auth Service"
        assert settings.VERSION == "1.0.0"
        assert settings.DESCRIPTION == "FastAPI Authentication Service with Circuit Breaker"
        assert settings.DEBUG is False

        # Database Configuration
        assert settings.SQLITE_DATABASE_URL == "sqlite:///./auth_service.db"
        assert settings.POSTGRES_SERVER is None
        assert settings.POSTGRES_USER is None
        assert settings.POSTGRES_PASSWORD is None
        assert settings.POSTGRES_DB is None

        # Security Configuration
        assert settings.PASSWORD_MIN_LENGTH == 8
        assert settings.PASSWORD_REQUIRE_SPECIAL is True
        assert settings.PASSWORD_REQUIRE_DIGIT is True
        assert settings.PASSWORD_REQUIRE_UPPERCASE is True
        assert settings.PASSWORD_REQUIRE_LOWERCASE is True

        # Rate Limiting Configuration
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100
        assert settings.RATE_LIMIT_WINDOW == 3600

        # Circuit Breaker Configuration
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
        assert settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 60

        # Logging Configuration
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_FORMAT == "json"
        assert settings.LOG_FILE is None

        # User Configuration
        assert settings.USERS_OPEN_REGISTRATION is True

    def test_settings_from_env(self, monkeypatch):
        """Test settings loaded from environment variables."""
        # Set environment variables
        monkeypatch.setenv("SECRET_KEY", "custom-secret-key")
        monkeypatch.setenv("PROJECT_NAME", "Custom Auth Service")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        monkeypatch.setenv("PASSWORD_MIN_LENGTH", "12")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")

        settings = Settings()

        assert settings.SECRET_KEY == "custom-secret-key"
        assert settings.PROJECT_NAME == "Custom Auth Service"
        assert settings.DEBUG is True
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.PASSWORD_MIN_LENGTH == 12
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.RATE_LIMIT_ENABLED is False

    def test_postgres_database_url_from_components(self):
        """Test PostgreSQL DATABASE_URL assembly from components."""
        settings = Settings(
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_DB="test_db"
        )

        expected_url = "postgresql+asyncpg://test_user:test_password@localhost/test_db"
        assert str(settings.DATABASE_URL) == expected_url

    def test_postgres_database_url_partial_components(self):
        """Test DATABASE_URL defaults to SQLite when PostgreSQL components are incomplete."""
        # Missing password
        settings = Settings(
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="test_user",
            POSTGRES_DB="test_db"
            # POSTGRES_PASSWORD is missing
        )

        # Should default to SQLite
        assert settings.DATABASE_URL == "sqlite:///./auth_service.db"

    def test_direct_database_url_override(self):
        """Test direct DATABASE_URL override."""
        direct_url = "postgresql+asyncpg://user:pass@host:5432/db"
        settings = Settings(DATABASE_URL=direct_url)

        assert str(settings.DATABASE_URL) == direct_url

    def test_cors_origins_string_parsing(self):
        """Test CORS origins parsing from string."""
        settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,https://app.example.com")

        assert settings.BACKEND_CORS_ORIGINS == [
            "http://localhost:3000",
            "https://app.example.com"
        ]

    def test_cors_origins_list_input(self):
        """Test CORS origins with list input."""
        origins = ["http://localhost:3000", "https://app.example.com"]
        settings = Settings(BACKEND_CORS_ORIGINS=origins)

        assert settings.BACKEND_CORS_ORIGINS == origins

    def test_cors_origins_empty_string(self):
        """Test CORS origins with empty string."""
        settings = Settings(BACKEND_CORS_ORIGINS="")

        assert settings.BACKEND_CORS_ORIGINS == [""]

    def test_invalid_cors_origins(self):
        """Test invalid CORS origins raise validation error."""
        with pytest.raises(ValidationError):
            Settings(BACKEND_CORS_ORIGINS=123)  # Invalid type

    def test_email_configuration(self):
        """Test email configuration settings."""
        settings = Settings(
            SMTP_TLS=False,
            SMTP_PORT=587,
            SMTP_HOST="smtp.example.com",
            SMTP_USER="test@example.com",
            SMTP_PASSWORD="smtp_password",
            EMAILS_FROM_EMAIL="noreply@example.com",
            EMAILS_FROM_NAME="Auth Service"
        )

        assert settings.SMTP_TLS is False
        assert settings.SMTP_PORT == 587
        assert settings.SMTP_HOST == "smtp.example.com"
        assert settings.SMTP_USER == "test@example.com"
        assert settings.SMTP_PASSWORD == "smtp_password"
        assert str(settings.EMAILS_FROM_EMAIL) == "noreply@example.com"
        assert settings.EMAILS_FROM_NAME == "Auth Service"

    def test_redis_configuration(self):
        """Test Redis configuration settings."""
        settings = Settings(
            REDIS_URL="redis://localhost:6379/0",
            REDIS_PREFIX="test_auth:"
        )

        assert settings.REDIS_URL == "redis://localhost:6379/0"
        assert settings.REDIS_PREFIX == "test_auth:"

    def test_monitoring_configuration(self):
        """Test monitoring configuration settings."""
        settings = Settings(
            ENABLE_METRICS=False,
            METRICS_PORT=9091,
            HEALTH_CHECK_INTERVAL=60,
            HEALTH_CHECK_TIMEOUT=10
        )

        assert settings.ENABLE_METRICS is False
        assert settings.METRICS_PORT == 9091
        assert settings.HEALTH_CHECK_INTERVAL == 60
        assert settings.HEALTH_CHECK_TIMEOUT == 10

    def test_superuser_configuration(self):
        """Test first superuser configuration."""
        settings = Settings(
            FIRST_SUPERUSER_EMAIL="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="admin_password"
        )

        assert str(settings.FIRST_SUPERUSER_EMAIL) == "admin@example.com"
        assert settings.FIRST_SUPERUSER_PASSWORD == "admin_password"

    def test_case_sensitive_config(self):
        """Test that configuration is case sensitive."""
        settings = Settings()

        # The Config class specifies case_sensitive = True
        assert settings.Config.case_sensitive is True

    def test_env_file_config(self):
        """Test environment file configuration."""
        settings = Settings()

        # Check env file configuration
        assert settings.Config.env_file == ".env"
        assert settings.Config.env_file_encoding == "utf-8"

    def test_settings_with_env_file(self):
        """Test settings loading from .env file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("SECRET_KEY=env-file-secret\n")
            f.write("PROJECT_NAME=Env File Auth Service\n")
            f.write("DEBUG=true\n")
            env_file_path = f.name

        try:
            # Test with explicit env_file
            class TestSettings(Settings):
                class Config(Settings.Config):
                    env_file = env_file_path

            settings = TestSettings()

            assert settings.SECRET_KEY == "env-file-secret"
            assert settings.PROJECT_NAME == "Env File Auth Service"
            assert settings.DEBUG is True

        finally:
            # Clean up
            os.unlink(env_file_path)

    def test_circuit_breaker_settings(self):
        """Test circuit breaker specific settings."""
        settings = Settings(
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=10,
            CIRCUIT_BREAKER_RECOVERY_TIMEOUT=120,
            CIRCUIT_BREAKER_EXPECTED_EXCEPTION="DatabaseException",
            CIRCUIT_BREAKER_FALLBACK_FUNCTION="fallback_handler"
        )

        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 10
        assert settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 120
        assert settings.CIRCUIT_BREAKER_EXPECTED_EXCEPTION == "DatabaseException"
        assert settings.CIRCUIT_BREAKER_FALLBACK_FUNCTION == "fallback_handler"

    def test_password_policy_settings(self):
        """Test password policy configuration."""
        settings = Settings(
            PASSWORD_MIN_LENGTH=12,
            PASSWORD_REQUIRE_SPECIAL=False,
            PASSWORD_REQUIRE_DIGIT=False,
            PASSWORD_REQUIRE_UPPERCASE=False,
            PASSWORD_REQUIRE_LOWERCASE=False
        )

        assert settings.PASSWORD_MIN_LENGTH == 12
        assert settings.PASSWORD_REQUIRE_SPECIAL is False
        assert settings.PASSWORD_REQUIRE_DIGIT is False
        assert settings.PASSWORD_REQUIRE_UPPERCASE is False
        assert settings.PASSWORD_REQUIRE_LOWERCASE is False

    def test_all_settings_types(self):
        """Test that all settings have correct types."""
        settings = Settings()

        # String settings
        assert isinstance(settings.API_V1_STR, str)
        assert isinstance(settings.SECRET_KEY, str)
        assert isinstance(settings.PROJECT_NAME, str)
        assert isinstance(settings.VERSION, str)
        assert isinstance(settings.DESCRIPTION, str)
        assert isinstance(settings.ALGORITHM, str)
        assert isinstance(settings.SQLITE_DATABASE_URL, str)
        assert isinstance(settings.LOG_LEVEL, str)
        assert isinstance(settings.LOG_FORMAT, str)
        assert isinstance(settings.CIRCUIT_BREAKER_EXPECTED_EXCEPTION, str)
        assert isinstance(settings.REDIS_PREFIX, str)

        # Integer settings
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert isinstance(settings.REFRESH_TOKEN_EXPIRE_DAYS, int)
        assert isinstance(settings.PASSWORD_MIN_LENGTH, int)
        assert isinstance(settings.RATE_LIMIT_REQUESTS, int)
        assert isinstance(settings.RATE_LIMIT_WINDOW, int)
        assert isinstance(settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD, int)
        assert isinstance(settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT, int)
        assert isinstance(settings.METRICS_PORT, int)
        assert isinstance(settings.HEALTH_CHECK_INTERVAL, int)
        assert isinstance(settings.HEALTH_CHECK_TIMEOUT, int)

        # Boolean settings
        assert isinstance(settings.DEBUG, bool)
        assert isinstance(settings.SMTP_TLS, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_SPECIAL, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_DIGIT, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_UPPERCASE, bool)
        assert isinstance(settings.PASSWORD_REQUIRE_LOWERCASE, bool)
        assert isinstance(settings.RATE_LIMIT_ENABLED, bool)
        assert isinstance(settings.ENABLE_METRICS, bool)
        assert isinstance(settings.USERS_OPEN_REGISTRATION, bool)

        # List settings
        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)