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


def test_occurrence_skip(tmp_path):
    """When occurrence is 'first_sunday' and today is NOT the first Sunday, post is skipped."""
    db = str(tmp_path / "test.db")
    # 2026-04-19 is a Sunday but the 3rd Sunday of April 2026
    mock_store = _make_store(
        campaign_type="reddit_comment",
        subs=[{"sub": "selfhosted", "active": 1, "occurrence": "first_sunday"}],
    )
    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            with patch("app.services.poster.date") as mock_date:
                from datetime import date as real_date
                mock_date.today.return_value = real_date(2026, 4, 19)
                result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="scheduler")

    assert result["skipped"] is True
    assert "occurrence" in result["reason"]
    mock_strategy.execute.assert_not_called()


def test_occurrence_passes(tmp_path):
    """When occurrence is 'first_sunday' and today IS the first Sunday, post proceeds."""
    db = str(tmp_path / "test.db")
    # 2026-05-03 is the first Sunday of May 2026
    mock_store = _make_store(
        campaign_type="reddit_comment",
        subs=[{"sub": "selfhosted", "active": 1, "occurrence": "first_sunday"}],
    )
    mock_result = MagicMock()
    mock_result.url = "https://reddit.com/r/selfhosted/comments/abc/"

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False
    mock_strategy.execute.return_value = mock_result

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            with patch("app.services.poster.date") as mock_date:
                from datetime import date as real_date
                mock_date.today.return_value = real_date(2026, 5, 3)
                result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="scheduler")

    assert result.get("status") == "success"
    mock_strategy.execute.assert_called_once()


def test_occurrence_every_passes_through(tmp_path):
    """occurrence='every' means post every time — no filtering, execute is called."""
    db = str(tmp_path / "test.db")
    # parse_occurrence("every") returns None → no filtering → execute runs
    mock_store = _make_store(
        campaign_type="reddit_comment",
        subs=[{"sub": "selfhosted", "active": 1, "occurrence": "every"}],
    )
    mock_result = MagicMock()
    mock_result.url = "https://reddit.com/r/selfhosted/comments/abc/"

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False
    mock_strategy.execute.return_value = mock_result

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            with patch("app.services.poster.date") as mock_date:
                from datetime import date as real_date
                mock_date.today.return_value = real_date(2026, 5, 3)
                result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="scheduler")

    assert result.get("status") == "success"
    mock_strategy.execute.assert_called_once()


def test_occurrence_none_sub_row_key_passes_through(tmp_path):
    """Sub row exists but has no occurrence key — should post normally."""
    db = str(tmp_path / "test.db")
    # sub_row has no "occurrence" key → .get() returns None → parse_occurrence(None) returns None
    mock_store = _make_store(
        campaign_type="reddit_comment",
        subs=[{"sub": "selfhosted", "active": 1}],
    )
    mock_result = MagicMock()
    mock_result.url = "https://reddit.com/r/selfhosted/comments/abc/"

    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False
    mock_strategy.execute.return_value = mock_result

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            with patch("app.services.poster.date") as mock_date:
                from datetime import date as real_date
                mock_date.today.return_value = real_date(2026, 5, 3)
                result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="scheduler")

    assert result.get("status") == "success"
    mock_strategy.execute.assert_called_once()


def test_occurrence_invalid_string_skips(tmp_path):
    """Malformed occurrence string results in skipped=True, not a crash."""
    db = str(tmp_path / "test.db")
    # "weekly" is not a valid occurrence string — parse_occurrence raises ValueError
    mock_store = _make_store(
        campaign_type="reddit_comment",
        subs=[{"sub": "selfhosted", "active": 1, "occurrence": "weekly"}],
    )
    mock_strategy = MagicMock()
    mock_strategy.supports_dupe_guard.return_value = False

    with patch("app.services.poster.Store", return_value=mock_store):
        with patch("app.services.poster.get_client", return_value=mock_strategy):
            with patch("app.services.poster.date") as mock_date:
                from datetime import date as real_date
                mock_date.today.return_value = real_date(2026, 5, 3)
                result = _run_post(db, campaign_id=1, target="selfhosted", triggered_by="scheduler")

    assert result.get("skipped") is True
    assert "invalid occurrence" in result.get("reason", "")
    mock_strategy.execute.assert_not_called()
