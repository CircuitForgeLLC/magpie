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

    # Session files — multi-user layout
    # sessions_dir holds per-account JSON files: alan_reddit.json, cf_reddit.json, etc.
    # reddit_session_file kept for backward compat; still used by the campaign scheduler
    # until all callers are migrated to look up session via team_accounts.
    sessions_dir: str = str(Path.home() / ".local" / "share" / "magpie" / "sessions")
    reddit_session_file: str = str(Path.home() / ".local" / "share" / "magpie" / "sessions" / "alan_reddit.json")

    # Scheduler
    scheduler_enabled: bool = True

    # Directus (CircuitForge website CMS)
    directus_url: str = "http://172.31.0.4:8055"
    directus_admin_token: str = ""
    directus_admin_email: str = ""
    directus_admin_password: str = ""
    directus_network: str = "website_cf-internal"

    # Signal scraper
    scraper_enabled: bool = True
    scraper_interval_mins: int = 30          # how often to poll (per full pass of all subs)
    scraper_request_delay_secs: float = 2.0  # pause between sub requests to respect rate limits
    scraper_fetch_limit: int = 25            # posts to fetch per sub per run (max 100)
    scraper_user_agent: str = "Magpie/0.1 signal-monitor (by CircuitForge)"


def get_settings() -> Settings:
    return Settings()
