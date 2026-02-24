from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    debug: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()