"""Reddit session management endpoints."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.reddit.session import ensure_valid_session, refresh_session, session_is_valid

router = APIRouter(tags=["reddit"])

BRIDGE_SESSION = Path("/Library/Development/CircuitForge/claude-bridge/reddit-poster/session.json")
BRIDGE_POST_SCRIPT = Path("/Library/Development/CircuitForge/claude-bridge/reddit-poster/post.py")


class SessionStatusResponse(BaseModel):
    target: str
    valid: bool
    age_hours: float | None
    session_file: str


class RefreshResponse(BaseModel):
    target: str
    ok: bool
    message: str


def _session_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return round((time.time() - path.stat().st_mtime) / 3600, 1)


@router.get("/reddit/session-status")
def session_status(target: str = "magpie") -> SessionStatusResponse:
    """Return session validity and age for magpie or bridge session."""
    if target == "bridge":
        valid = BRIDGE_SESSION.exists() and _session_age_hours(BRIDGE_SESSION) < 12
        return SessionStatusResponse(
            target="bridge",
            valid=valid,
            age_hours=_session_age_hours(BRIDGE_SESSION),
            session_file=str(BRIDGE_SESSION),
        )
    # magpie session
    from app.core.config import get_settings
    session_file = Path(get_settings().reddit_session_file)
    return SessionStatusResponse(
        target="magpie",
        valid=session_is_valid(session_file),
        age_hours=_session_age_hours(session_file),
        session_file=str(session_file),
    )


@router.post("/reddit/refresh-session")
def refresh_reddit_session(target: str = "magpie") -> RefreshResponse:
    """
    Re-establish the Playwright Reddit session.

    target: "magpie" (default) refreshes Magpie's session.
            "bridge" refreshes claude-bridge/reddit-poster/session.json.
    """
    if target == "bridge":
        if not BRIDGE_POST_SCRIPT.exists():
            raise HTTPException(status_code=404, detail="claude-bridge post.py not found")
        result = subprocess.run(
            ["xvfb-run", "--auto-servernum", sys.executable, str(BRIDGE_POST_SCRIPT), "--login"],
            cwd=str(BRIDGE_POST_SCRIPT.parent),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Bridge session refresh failed: {result.stderr.strip()}",
            )
        return RefreshResponse(target="bridge", ok=True, message="Bridge session refreshed.")

    # magpie session
    try:
        from app.core.config import get_settings
        session_file = Path(get_settings().reddit_session_file)
        refresh_session(session_file)
        return RefreshResponse(target="magpie", ok=True, message="Magpie session refreshed.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
