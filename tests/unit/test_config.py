"""
Test the configuration management.
"""

import pytest
from app.core.config import Settings, DatabaseSettings, JWTSettings, IntegrationSettings


def test_default_settings():
    """Test default settings values."""
    settings = Settings()

    assert settings.app_name == "Insurance Management System"
    assert settings.app_version == "1.0.0"
    assert settings.environment == "development"
    assert settings.debug is False


def test_database_settings():
    """Test database configuration."""
    db_settings = DatabaseSettings()

    assert "sqlite+aiosqlite" in db_settings.sqlite_url
    assert db_settings.postgresql_url is None
    assert db_settings.echo is False
    assert db_settings.pool_size == 5
    assert db_settings.max_overflow == 10


def test_jwt_settings():
    """Test JWT configuration."""
    jwt_settings = JWTSettings()

    assert len(jwt_settings.secret_key) >= 32
    assert jwt_settings.algorithm == "HS256"
    assert jwt_settings.access_token_expire_minutes == 30
    assert jwt_settings.refresh_token_expire_days == 7


def test_integration_settings():
    """Test integration configuration."""
    int_settings = IntegrationSettings()

    assert int_settings.stripe_secret_key is None
    assert int_settings.stripe_publishable_key is None
    assert int_settings.banking_api_key is None
    assert int_settings.circuit_breaker_failure_threshold == 5
    assert int_settings.circuit_breaker_reset_timeout == 60


def test_database_url_property():
    """Test database URL selection logic."""
    settings = Settings()

    # Development should use SQLite
    assert "sqlite" in settings.database_url

    # Production with PostgreSQL URL should use PostgreSQL
    settings.environment = "production"
    settings.database.postgresql_url = "postgresql+asyncpg://test:test@localhost/test"
    assert "postgresql" in settings.database_url


def test_environment_properties():
    """Test environment detection properties."""
    settings = Settings()

    # Development
    settings.environment = "development"
    assert settings.is_development is True
    assert settings.is_production is False

    # Production
    settings.environment = "production"
    assert settings.is_development is False
    assert settings.is_production is True


def test_jwt_backward_compatibility():
    """Test JWT settings backward compatibility."""
    settings = Settings()

    jwt = settings.jwt
    assert isinstance(jwt, JWTSettings)
    assert jwt.secret_key == settings.jwt_secret_key
    assert jwt.algorithm == settings.jwt_algorithm