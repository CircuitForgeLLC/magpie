from unittest.mock import MagicMock, patch

from app.services.platforms.reddit_post import RedditPostStrategy
from app.services.platforms.base import PostResult


def test_execute_delegates_to_reddit_client(tmp_path):
    session_file = tmp_path / "session.json"
    session_file.write_text('{"cookies": [], "origins": []}')

    mock_client = MagicMock()
    mock_client.post.return_value = "https://reddit.com/r/test/comments/abc/title/"

    with patch("app.services.platforms.reddit_post.RedditClient", return_value=mock_client):
        with patch("app.services.platforms.reddit_post.get_settings") as mock_settings:
            mock_settings.return_value.reddit_session_file = str(session_file)
            strategy = RedditPostStrategy()
            result = strategy.execute(
                target="selfhosted",
                title="Test Title",
                body="Test body",
                flair="Showcase",
            )

    mock_client.post.assert_called_once_with(
        sub="selfhosted",
        title="Test Title",
        body="Test body",
        flair="Showcase",
    )
    assert isinstance(result, PostResult)
    assert result.url == "https://reddit.com/r/test/comments/abc/title/"


def test_execute_propagates_client_error(tmp_path):
    session_file = tmp_path / "session.json"
    session_file.write_text('{"cookies": [], "origins": []}')

    mock_client = MagicMock()
    mock_client.post.side_effect = RuntimeError("Playwright timeout")

    with patch("app.services.platforms.reddit_post.RedditClient", return_value=mock_client):
        with patch("app.services.platforms.reddit_post.get_settings") as mock_settings:
            mock_settings.return_value.reddit_session_file = str(session_file)
            strategy = RedditPostStrategy()
            try:
                strategy.execute(target="selfhosted", title="T", body="B")
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert "Playwright timeout" in str(e)


def test_campaign_type():
    assert RedditPostStrategy.campaign_type == "reddit_post"


def test_supports_dupe_guard():
    assert RedditPostStrategy().supports_dupe_guard() is True
