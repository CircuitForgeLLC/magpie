from __future__ import annotations

from app.core.config import get_settings
from app.services.platforms.base import PostingStrategy, PostResult
from app.services.reddit.client import RedditClient


class RedditPostStrategy(PostingStrategy):
    """Submit a new Reddit text post via RedditClient (Playwright subprocess)."""

    campaign_type = "reddit_post"

    def execute(
        self,
        *,
        target: str,
        title: str,
        body: str,
        flair: str | None = None,
        extra: dict | None = None,
    ) -> PostResult:
        settings = get_settings()
        client = RedditClient(session_file=settings.reddit_session_file)
        link_url = (extra or {}).get("link_url") or None
        url = client.post(sub=target, title=title, body=body, flair=flair, link_url=link_url)
        return PostResult(url=url)
