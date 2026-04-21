from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8532
    debug: bool = False

    # Database
    db_path: str = str(Path.home() / ".local" / "share" / "magpie" / "magpie.db")

    # Reddit session
    reddit_session_file: str = str(Path.home() / ".local" / "share" / "magpie" / "session.json")

    # Scheduler
    scheduler_enabled: bool = True


def get_settings() -> Settings:
    return Settings()
