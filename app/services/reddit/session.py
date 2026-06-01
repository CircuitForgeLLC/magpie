"""
Reddit session management via Playwright + xvfb-run.

Migrated from claude-bridge/reddit-poster/reddit.py.
Session cookies are stored in a JSON file and refreshed automatically when stale.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from app.core.config import get_settings

SESSION_MAX_AGE_HOURS = 12
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0.0.0"

_POST_SCRIPT = Path(__file__).parent / "post.py"


def _session_age_hours(session_file: Path) -> float:
    if not session_file.exists():
        return float("inf")
    return (time.time() - session_file.stat().st_mtime) / 3600


def session_is_valid(session_file: Path | None = None) -> bool:
    if session_file is None:
        session_file = Path(get_settings().reddit_session_file)
    return _session_age_hours(session_file) < SESSION_MAX_AGE_HOURS


def refresh_session(session_file: Path | None = None) -> None:
    """Re-login via Playwright (xvfb-run) and overwrite the session file."""
    if session_file is None:
        session_file = Path(get_settings().reddit_session_file)
    session_file.parent.mkdir(parents=True, exist_ok=True)
    print("Session expired or missing — re-establishing via Playwright login...")
    result = subprocess.run(
        ["xvfb-run", "--auto-servernum", sys.executable, str(_POST_SCRIPT), "--login"],
        cwd=str(_POST_SCRIPT.parent),
        env={**os.environ, "REDDIT_SESSION_FILE": str(session_file)},
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError("Playwright re-login failed. Check credentials in .env.")
    print("Session refreshed.")


def load_cookies(session_file: Path | None = None) -> dict[str, str]:
    if session_file is None:
        session_file = Path(get_settings().reddit_session_file)
    if not session_file.exists():
        refresh_session(session_file)
    state = json.loads(session_file.read_text())
    return {c["name"]: c["value"] for c in state.get("cookies", [])}


def ensure_valid_session(session_file: Path | None = None) -> None:
    if session_file is None:
        session_file = Path(get_settings().reddit_session_file)
    if not session_is_valid(session_file):
        refresh_session(session_file)
