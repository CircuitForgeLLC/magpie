from datetime import date
from unittest.mock import MagicMock
import pytest
from app.services.platforms.reddit_comment import (
    is_nth_weekday,
    parse_occurrence,
    _extract_thread_id_from_url,
    _find_sticky,
)


# --- is_nth_weekday ---

def test_first_sunday_of_april_2026():
    # 2026-04-05 is the first Sunday of April 2026
    assert is_nth_weekday(date(2026, 4, 5), weekday=6, n=1) is True


def test_second_sunday_of_april_2026_is_not_first():
    assert is_nth_weekday(date(2026, 4, 12), weekday=6, n=1) is False


def test_first_sunday_of_may_2026():
    # 2026-05-03 is the first Sunday of May 2026
    assert is_nth_weekday(date(2026, 5, 3), weekday=6, n=1) is True


def test_last_friday_not_matched_by_first():
    # 2026-04-24 is the last Friday of April — not the first
    assert is_nth_weekday(date(2026, 4, 24), weekday=4, n=1) is False


def test_first_friday_of_april_2026():
    # 2026-04-03 is the first Friday
    assert is_nth_weekday(date(2026, 4, 3), weekday=4, n=1) is True


# --- parse_occurrence ---

def test_parse_occurrence_every_returns_none():
    assert parse_occurrence("every") is None


def test_parse_occurrence_none_returns_none():
    assert parse_occurrence(None) is None


def test_parse_occurrence_first_sunday():
    weekday, n = parse_occurrence("first_sunday")
    assert weekday == 6 and n == 1


def test_parse_occurrence_unknown_raises():
    with pytest.raises(ValueError):
        parse_occurrence("fourth_wednesday")


# --- _extract_thread_id_from_url ---

def test_extract_thread_id_success():
    url = "https://www.reddit.com/r/flipping/comments/abc123/weekly_thread/"
    assert _extract_thread_id_from_url(url) == "abc123"


def test_extract_thread_id_invalid():
    with pytest.raises(ValueError):
        _extract_thread_id_from_url("https://www.reddit.com/r/flipping/")


# --- _find_sticky ---

def _make_hot_json(posts: list[dict]) -> dict:
    """Build a fake Reddit hot.json payload."""
    return {"data": {"children": [{"data": p} for p in posts]}}


def test_find_sticky_found(monkeypatch):
    fake_response = MagicMock()
    fake_response.json.return_value = _make_hot_json([
        {"id": "abc123", "title": "Weekly Self-Promotion Thread"},
        {"id": "xyz999", "title": "General Discussion"},
    ])

    import app.services.platforms.reddit_comment as rc_module
    monkeypatch.setattr(rc_module.httpx, "get", lambda *a, **kw: fake_response)

    result = _find_sticky("flipping", "Self-Promotion")
    assert result == "abc123"


def test_find_sticky_not_found(monkeypatch):
    fake_response = MagicMock()
    fake_response.json.return_value = _make_hot_json([
        {"id": "xyz999", "title": "General Discussion"},
    ])

    import app.services.platforms.reddit_comment as rc_module
    monkeypatch.setattr(rc_module.httpx, "get", lambda *a, **kw: fake_response)

    result = _find_sticky("flipping", "Self-Promotion")
    assert result is None
