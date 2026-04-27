import pytest
from app.services.platforms import get_client, SUPPORTED_PLATFORMS
from app.services.platforms.reddit_post import RedditPostStrategy
from app.services.platforms.blog_post import BlogPostStrategy


def test_get_client_returns_reddit_post_strategy():
    client = get_client("reddit_post")
    assert isinstance(client, RedditPostStrategy)


def test_get_client_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown campaign type"):
        get_client("nonexistent_type")


def test_supported_platforms_contains_reddit_post():
    assert "reddit_post" in SUPPORTED_PLATFORMS


def test_get_client_returns_blog_post_strategy():
    client = get_client("blog_post")
    assert isinstance(client, BlogPostStrategy)


def test_supported_platforms_contains_blog_post():
    assert "blog_post" in SUPPORTED_PLATFORMS
