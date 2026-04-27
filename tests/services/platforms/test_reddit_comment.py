from datetime import date
from app.services.platforms.reddit_comment import is_nth_weekday, parse_occurrence


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
    try:
        parse_occurrence("fourth_wednesday")
        assert False, "Expected ValueError"
    except ValueError:
        pass
