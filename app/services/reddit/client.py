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
        self._session_file = Path(session_file) if session_file else Path(settings.reddit_session_file)
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
        """Submit a text post via Reddit legacy API (httpx). Returns the permalink."""
        data = {
            "api_type": "json",
            "kind": "self",
            "sr": sub,
            "title": title,
            "text": body,
            "uh": self.modhash,
            "sendreplies": "true",
            "nsfw": "false",
            "spoiler": "false",
        }
        resp = httpx.post(
            "https://www.reddit.com/api/submit",
            cookies=self.cookies,
            headers=self.headers,
            data=data,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        errors = result.get("json", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Post to r/{sub} failed: {errors}")
        url = result.get("json", {}).get("data", {}).get("url", "")
        if not url:
            raise RuntimeError(
                f"Post to r/{sub} may have failed — no URL in response:\n{result}"
            )
        return url

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
