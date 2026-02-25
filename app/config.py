from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "sqlite:///./dev.db"
    debug: bool = False
    jwt_secret: str = "dev-secret-key-change-in-production"
    jwt_expiration: int = 3600  # seconds (1 hour)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
