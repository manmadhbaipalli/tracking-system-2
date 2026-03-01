from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Auth App"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./auth.db"

    # JWT
    jwt_secret: str = Field(default="dev-secret-change-in-production-min-32-chars-for-security")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # CORS
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # Server
    server_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
