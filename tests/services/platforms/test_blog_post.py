import json
from unittest.mock import patch

import pytest

from app.services.platforms.blog_post import BlogPostStrategy
from app.services.platforms.base import PostResult


def _make_directus_response(slug: str = "test-post", post_id: int = 42) -> dict:
    return {"id": post_id, "slug": slug, "title": "Test Post", "status": "published"}


def test_campaign_type():
    assert BlogPostStrategy.campaign_type == "blog_post"


def test_does_not_support_dupe_guard():
    assert BlogPostStrategy().supports_dupe_guard() is False


def test_execute_publishes_immediately():
    mock_response = _make_directus_response(slug="my-post")

    with patch("app.services.platforms.blog_post.publish_blog_post", return_value=mock_response) as mock_pub:
        strategy = BlogPostStrategy()
        result = strategy.execute(
            target="blog/main",
            title="My Test Post",
            body="# Hello\n\nThis is the post body.",
        )

    mock_pub.assert_called_once_with(
        title="My Test Post",
        body="# Hello\n\nThis is the post body.",
        slug=None,
        tags=None,
        seo_description=None,
    )
    assert isinstance(result, PostResult)
    assert result.url == "https://circuitforge.tech/blog/my-post"
    assert result.metadata["directus_id"] == 42


def test_execute_passes_extra_fields():
    mock_response = _make_directus_response(slug="custom-slug")

    with patch("app.services.platforms.blog_post.publish_blog_post", return_value=mock_response) as mock_pub:
        strategy = BlogPostStrategy()
        result = strategy.execute(
            target="blog/main",
            title="Custom Slug Post",
            body="Body content here.",
            extra={
                "slug": "custom-slug",
                "tags": ["self-hosting", "peregrine"],
                "seo_description": "A short description for SEO.",
            },
        )

    mock_pub.assert_called_once_with(
        title="Custom Slug Post",
        body="Body content here.",
        slug="custom-slug",
        tags=["self-hosting", "peregrine"],
        seo_description="A short description for SEO.",
    )
    assert result.url == "https://circuitforge.tech/blog/custom-slug"


def test_execute_parses_tags_from_json_string():
    """Tags stored as JSON string in campaign_variants.tags should be decoded."""
    mock_response = _make_directus_response(slug="json-tags-post")

    with patch("app.services.platforms.blog_post.publish_blog_post", return_value=mock_response) as mock_pub:
        strategy = BlogPostStrategy()
        strategy.execute(
            target="blog/main",
            title="JSON Tags Post",
            body="Body.",
            extra={"tags": '["self-hosting","kiwi"]'},  # stored as JSON string
        )

    call_args = mock_pub.call_args
    assert call_args.kwargs["tags"] == ["self-hosting", "kiwi"]


def test_execute_raises_on_directus_error():
    with patch("app.services.platforms.blog_post.publish_blog_post",
               side_effect=RuntimeError("Directus 502")):
        strategy = BlogPostStrategy()
        with pytest.raises(RuntimeError, match="Directus 502"):
            strategy.execute(target="blog/main", title="T", body="B")
