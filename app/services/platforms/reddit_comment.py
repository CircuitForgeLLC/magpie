from __future__ import annotations

import logging
import re
from datetime import date, timedelta

import httpx

from app.services.platforms.base import PostingStrategy, PostResult

logger = logging.getLogger(__name__)

# Weekday names → int (0=Mon, 6=Sun)
_WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}
# Ordinal names → n
_ORDINAL_MAP = {"first": 1, "second": 2, "third": 3}


def is_nth_weekday(dt: date, weekday: int, n: int) -> bool:
    """True if dt is the nth occurrence of weekday (0=Mon, 6=Sun) in its month."""
    first_of_month = dt.replace(day=1)
    days_until = (weekday - first_of_month.weekday()) % 7
    first_occurrence = first_of_month + timedelta(days=days_until)
    nth_occurrence = first_occurrence + timedelta(weeks=n - 1)
    return dt == nth_occurrence


def parse_occurrence(occurrence: str | None) -> tuple[int, int] | None:
    """Parse an occurrence string into (weekday, n) or None for 'every'.

    Supported: "first_sunday", "second_monday", "third_friday", etc.
    Returns None for "every" or None input.
    Raises ValueError for unrecognised patterns.
    """
    if occurrence is None or occurrence == "every":
        return None
    parts = occurrence.lower().split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Unrecognised occurrence format: {occurrence!r}")
    ordinal, weekday_name = parts
    if ordinal not in _ORDINAL_MAP or weekday_name not in _WEEKDAY_MAP:
        raise ValueError(f"Unrecognised occurrence: {occurrence!r}")
    return _WEEKDAY_MAP[weekday_name], _ORDINAL_MAP[ordinal]


def _extract_thread_id_from_url(url: str) -> str:
    """Extract a Reddit post ID from a full Reddit URL.

    Expects URLs of the form:
        https://www.reddit.com/r/<sub>/comments/<id>/<title>/
    Raises ValueError if the ID cannot be found.
    """
    match = re.search(r"/comments/([a-zA-Z0-9]+)/", url)
    if not match:
        raise ValueError(f"Cannot extract thread id from {url!r}")
    return match.group(1)


def _find_sticky(
    sub: str,
    title_pattern: str,
    session_file: str | None = None,
) -> str | None:
    """Search the hot listing of a subreddit for a post matching title_pattern.

    Uses the Reddit public JSON API (no auth required).
    Returns the post ID (e.g. "abc123") of the first match, or None.
    """
    # TODO: use session_file for authenticated requests on private subs
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
    response = httpx.get(url, headers={"User-Agent": "magpie/1.0"})
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload:
        logger.warning("Unexpected Reddit API response: %r", payload)
        return None
    children = payload.get("data", {}).get("children", [])
    pattern_lower = title_pattern.lower()
    for child in children:
        post = child.get("data", {})
        title = post.get("title", "")
        if pattern_lower in title.lower():
            return post.get("id")
    return None
