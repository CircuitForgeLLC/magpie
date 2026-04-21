"""
RedditClient: thin wrapper around the Playwright post.py script.

Migrated from claude-bridge/reddit-poster/reddit.py.
Posting goes via xvfb-run + Playwright (avoids Reddit API bot detection).
Comment/delete go via httpx with saved session cookies.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.services.reddit.session import ensure_valid_session, load_cookies

_POST_SCRIPT = Path(__file__).parent / "post.py"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0.0.0"


class RedditClient:
    def __init__(self, session_file: Path | None = None) -> None:
        settings = get_settings()
        self._session_file = session_file or Path(settings.reddit_session_file)
        ensure_valid_session(self._session_file)
        self.cookies = load_cookies(self._session_file)
        self.headers = {"User-Agent": USER_AGENT}
        self._modhash: str | None = None

    @property
    def modhash(self) -> str:
        if self._modhash is None:
            resp = httpx.get(
                "https://www.reddit.com/api/me.json",
                cookies=self.cookies,
                headers=self.headers,
                timeout=15,
            )
            self._modhash = resp.json().get("data", {}).get("modhash", "")
        return self._modhash

    def post(self, sub: str, title: str, body: str, flair: str | None = None) -> str:
        """Submit a text post via Playwright (xvfb-run). Returns the permalink."""
        settings = get_settings()
        cmd = [
            "xvfb-run", "--auto-servernum",
            sys.executable, str(_POST_SCRIPT),
            "--sub", sub,
            "--title", title,
            "--body", body,
            "--yes",
        ]
        if flair:
            cmd += ["--flair", flair]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            env={
                **__import__("os").environ,
                "REDDIT_SESSION_FILE": str(self._session_file),
            },
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Post to r/{sub} failed (exit {result.returncode}):\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        for line in result.stdout.splitlines():
            if line.startswith("Posted:"):
                url = line.split("Posted:", 1)[-1].strip()
                return url
        raise RuntimeError(
            f"Post to r/{sub} may have failed — no 'Posted:' line in output.\n"
            f"Full stdout:\n{result.stdout}"
        )

    def comment(self, thread_id: str, body: str) -> str:
        """Post a top-level comment to a thread. Returns the permalink."""
        resp = httpx.post(
            "https://www.reddit.com/api/comment",
            cookies=self.cookies,
            headers={**self.headers, "X-Modhash": self.modhash},
            data={
                "api_type": "json",
                "thing_id": f"t3_{thread_id}",
                "text": body,
            },
            timeout=15,
        )
        result = resp.json()
        errors = result.get("json", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Comment failed: {errors}")
        things = result.get("json", {}).get("data", {}).get("things", [])
        permalink = (
            "https://reddit.com" + things[0]["data"].get("permalink", "") if things else ""
        )
        return permalink

    def delete(self, post_url: str) -> None:
        """Delete a post by URL."""
        import re
        match = re.search(r"/comments/([a-z0-9]+)/", post_url)
        if not match:
            raise ValueError(f"Cannot extract post ID from: {post_url}")
        post_id = match.group(1)
        resp = httpx.post(
            "https://www.reddit.com/api/del",
            cookies=self.cookies,
            headers={**self.headers, "X-Modhash": self.modhash},
            data={"id": f"t3_{post_id}"},
            timeout=15,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Delete failed ({resp.status_code}): {resp.text[:200]}")
