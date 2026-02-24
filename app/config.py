from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = "auth-service"
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # JWT
    jwt_secret: str = Field(default="dev-secret-change-in-production-min-32-chars")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # CORS
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # Rate limiting (failed login attempts)
    max_login_attempts: int = 5
    login_attempt_window_minutes: int = 60

    # Server
    server_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
