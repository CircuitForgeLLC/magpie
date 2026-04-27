from __future__ import annotations

import json
import logging

from app.services.directus import publish_blog_post
from app.services.platforms.base import PostingStrategy, PostResult

logger = logging.getLogger(__name__)

_BLOG_BASE_URL = "https://circuitforge.tech/blog"


class BlogPostStrategy(PostingStrategy):
    """Publish a blog post to the CircuitForge website via Directus.

    target: arbitrary label string (e.g. "blog/main") — used for logging only.
    title:  post title
    body:   post body (Markdown)
    extra:  optional dict with keys:
        slug            (str)       — Directus URL slug; generated from title if absent
        tags            (list|str)  — tag list or JSON-encoded list string
        seo_description (str)       — meta description
    """

    campaign_type = "blog_post"

    def execute(
        self,
        *,
        target: str,
        title: str,
        body: str,
        flair: str | None = None,
        extra: dict | None = None,
    ) -> PostResult:
        extra = extra or {}

        slug = extra.get("slug") or None
        seo_description = extra.get("seo_description") or None

        # tags may be stored as a JSON string in the DB; decode it
        raw_tags = extra.get("tags")
        tags: list[str] | None = None
        if isinstance(raw_tags, str):
            try:
                tags = json.loads(raw_tags)
            except json.JSONDecodeError:
                logger.warning("Could not parse tags JSON: %r", raw_tags)
        elif isinstance(raw_tags, list):
            tags = raw_tags

        item = publish_blog_post(
            title=title,
            body=body,
            slug=slug,
            tags=tags,
            seo_description=seo_description,
        )

        published_slug = item.get("slug", slug or "")
        url = f"{_BLOG_BASE_URL}/{published_slug}"

        return PostResult(
            url=url,
            metadata={"directus_id": item.get("id"), "slug": published_slug},
        )

    def supports_dupe_guard(self) -> bool:
        return False
