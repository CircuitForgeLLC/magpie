from unittest.mock import MagicMock, patch
from app.services.poster import _run_post


def _make_store(
    *,
    already_posted=False,
    variant=None,
    rules=None,
    campaign_type="reddit_post",
    subs=None,
):
    store = MagicMock()
    store.already_posted_this_week.return_value = already_posted
    store.resolve_variant.return_value = variant or {
        "id": 1,
        "title": "Test Title",
        "body": "Test body",
        "flair": None,
    }
    store.get_sub_rules.return_value = rules
    store.get_campaign.return_value = {
        "id": 1,
        "name": "Test",
        "type": campaign_type,
        "platform": "reddit",
    }
    store.create_post.return_value = {"id": 42}
    store.update_post_status.return_value = {
        "id": 42, "status": "success",
        "url": "https://reddit.com/r/test/comments/abc/",
    }
    store.list_campaign_subs.return_value = subs or []
    return store


def test_run_post_dispatches_by_campaign_type(tmp_path):
    db = str(tmp_path / "test.db")
    mock_store = _make_store()

    mock_result = MagicMock()
    mock_result.url = "https://reddit.com/r/test/comments/abc/"

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = True
    mock_strategy.execute.return_value = mock_result

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy) as mock_get_client:
            result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="manual")

    mock_get_client.assert_called_once_with("reddit_post")
    mock_strategy.execute.assert_called_once()
    assert result["status"] == "success"


def test_run_post_skips_when_dupe_guard_fires(tmp_path):
    db = str(tmp_path / "test.db")
    mock_store = _make_store(already_posted=True)

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = True

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="manual")

    assert result["skipped"] is True
    mock_strategy.execute.assert_not_called()


def test_run_post_skips_dupe_guard_when_strategy_opts_out(tmp_path):
    db = str(tmp_path / "test.db")
    mock_store = _make_store(already_posted=True, campaign_type="blog_post")

    mock_result = MagicMock()
    mock_result.url = "https://circuitforge.tech/blog/test-post"

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False
    mock_strategy.execute.return_value = mock_result

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            result = _run_post(db, campaign_id=1, target="blog", triggered_by="scheduler")

    mock_strategy.execute.assert_called_once()
    assert result["status"] == "success"


def test_run_post_skips_banned_sub(tmp_path):
    db = str(tmp_path / "test.db")
    mock_store = _make_store(rules={"promo_allowed": 0})

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = True

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            result = _run_post(db, campaign_id=1, target="ADHD", triggered_by="scheduler")

    assert result["skipped"] is True
    mock_strategy.execute.assert_not_called()


def test_run_post_unknown_type_skips(tmp_path):
    db = str(tmp_path / "test.db")
    mock_store = _make_store(campaign_type="future_platform")

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", side_effect=ValueError("Unknown campaign type")):
            result = _run_post(db, campaign_id=1, target="some_target", triggered_by="scheduler")

    assert result["skipped"] is True
    assert "Unknown campaign type" in result["reason"]
