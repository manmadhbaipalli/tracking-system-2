"""Configuration settings for FastAPI application."""

import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration based on environment."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    environment: str = os.getenv("ENVIRONMENT", "dev")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./test.db" if os.getenv("ENVIRONMENT") == "test"
        else "sqlite:///./app.db"
    )
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "secret")
    jwt_algorithm: str = "HS256"
    token_expiry_minutes: int = 1440  # 24 hours
    debug: bool = environment == "dev"


settings = Settings()
