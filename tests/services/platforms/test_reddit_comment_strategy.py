from unittest.mock import patch, MagicMock
import pytest
from app.services.platforms.reddit_comment import RedditCommentStrategy
from app.services.platforms.base import PostResult


@pytest.fixture
def strategy():
    return RedditCommentStrategy()


def test_execute_with_url_override(strategy, monkeypatch):
    """Uses thread_url_override to get thread_id, calls client.comment()"""
    mock_client = MagicMock()
    mock_client.comment.return_value = "https://www.reddit.com/r/flipping/comments/abc123/_/xyz789/"
    with patch("app.services.platforms.reddit_comment.RedditClient", return_value=mock_client):
        with patch("app.services.platforms.reddit_comment.get_settings") as mock_settings:
            mock_settings.return_value.reddit_session_file = "/fake/session.json"
            result = strategy.execute(
                target="flipping",
                title="ignored",
                body="Hello thread!",
                extra={"thread_url_override": "https://www.reddit.com/r/flipping/comments/abc123/weekly/"},
            )
    assert result.url == "https://www.reddit.com/r/flipping/comments/abc123/_/xyz789/"
    assert result.metadata["thread_id"] == "abc123"
    mock_client.comment.assert_called_once_with(thread_id="abc123", body="Hello thread!")


def test_execute_with_title_pattern_found(strategy):
    """Uses _find_sticky to locate thread, posts comment"""
    with patch("app.services.platforms.reddit_comment._find_sticky", return_value="def456"):
        with patch("app.services.platforms.reddit_comment.RedditClient") as MockClient:
            with patch("app.services.platforms.reddit_comment.get_settings") as mock_settings:
                mock_settings.return_value.reddit_session_file = "/fake/session.json"
                MockClient.return_value.comment.return_value = ""
                result = strategy.execute(
                    target="cscareerquestions",
                    title="ignored",
                    body="Job search tool",
                    extra={"thread_title_pattern": "Monthly Resume"},
                )
    assert "def456" in result.url
    assert result.metadata["thread_id"] == "def456"


def test_execute_thread_not_found(strategy):
    """Raises ValueError when _find_sticky returns None"""
    with patch("app.services.platforms.reddit_comment._find_sticky", return_value=None):
        with patch("app.services.platforms.reddit_comment.get_settings") as mock_settings:
            mock_settings.return_value.reddit_session_file = "/fake/session.json"
            with pytest.raises(ValueError, match="No thread matching"):
                strategy.execute(
                    target="cscareerquestions",
                    title="ignored",
                    body="body",
                    extra={"thread_title_pattern": "Monthly Resume"},
                )


def test_execute_no_extra_raises(strategy):
    """Raises ValueError when neither thread_url_override nor thread_title_pattern provided"""
    with patch("app.services.platforms.reddit_comment.get_settings") as mock_settings:
        mock_settings.return_value.reddit_session_file = "/fake/session.json"
        with pytest.raises(ValueError, match="requires thread_url_override or thread_title_pattern"):
            strategy.execute(target="flipping", title="t", body="b", extra={})


def test_reconstructed_url_on_empty_comment_url(strategy):
    """When client.comment() returns empty string, reconstructs URL from thread_id"""
    with patch("app.services.platforms.reddit_comment.RedditClient") as MockClient:
        with patch("app.services.platforms.reddit_comment.get_settings") as mock_settings:
            mock_settings.return_value.reddit_session_file = "/fake/session.json"
            MockClient.return_value.comment.return_value = ""
            result = strategy.execute(
                target="flipping",
                title="t",
                body="b",
                extra={"thread_url_override": "https://www.reddit.com/r/flipping/comments/abc123/weekly/"},
            )
    assert result.url == "https://www.reddit.com/r/flipping/comments/abc123/"


def test_supports_dupe_guard_false(strategy):
    assert strategy.supports_dupe_guard() is False


def test_registry_contains_reddit_comment():
    from app.services.platforms import _REGISTRY
    assert "reddit_comment" in _REGISTRY
