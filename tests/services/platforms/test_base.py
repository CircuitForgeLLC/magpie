from app.services.platforms.base import PostResult


def test_post_result_requires_url():
    r = PostResult(url="https://reddit.com/r/test/comments/abc")
    assert r.url == "https://reddit.com/r/test/comments/abc"
    assert r.metadata is None


def test_post_result_accepts_metadata():
    r = PostResult(url="https://example.com", metadata={"id": "abc123"})
    assert r.metadata == {"id": "abc123"}
