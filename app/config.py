from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    secret_key: str = ""
    access_token_expire_minutes: int = 60
    bcrypt_rounds: int = 12
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    app_env: str = "development"
    docs_enabled: bool = True
    cb_failure_threshold: int = 5
    cb_open_duration_seconds: int = 30
    db_pool_size: int = 5
    debug: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
