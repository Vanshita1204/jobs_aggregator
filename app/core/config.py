# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    SECRET_KEY: str
    DATABASE_URL: str
    NEW_JOB_THRESHOLD_HOURS: int = 24
    PLAYWRIGHT_HEADLESS: bool = False  # overridden to True in Docker via docker-compose
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
