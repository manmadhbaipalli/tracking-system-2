from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "simple-python-app"
    environment: str = "development"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./dev.db"

    jwt_secret: str = Field(default="dev-secret-change-in-production-min-32-chars")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    cors_allowed_origins: str = "http://localhost:3000"

    server_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
