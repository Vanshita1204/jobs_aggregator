# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    SECRET_KEY: str
    DATABASE_URL: str
    NEW_JOB_THRESHOLD_HOURS: int = 24
    DESCRIPTION_BACKFILL_DAILY_LIMIT: int = 200  # cap per day so a large backlog can't turn into an hours-long task or burst-hammer source sites
    PLAYWRIGHT_HEADLESS: bool = True  # override to False in .env for local dev if you want to watch the browser
    REDIS_URL: str = "redis://localhost:6379/0"
    GROQ_API_KEY: str = ""
    GCS_BUCKET: str = "job-aggregator-cvs"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
