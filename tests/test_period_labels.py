"""Boundary tests for constants.period_labels (Year / Month / Week-of-month, Sunday-start)."""
import datetime as dt

from constants import period_labels


def w(d: str) -> dict:
    return period_labels(dt.date.fromisoformat(d))


def test_sunday_start_first_week():
    # 2026-03-01 is a Sunday -> week 1 begins on it
    assert w("2026-03-01") == {"Year": "2026", "Month": "2026 03월", "Week": "2026 03월 1주"}
    assert w("2026-03-07")["Week"] == "2026 03월 1주"   # Sat, same week
    assert w("2026-03-08")["Week"] == "2026 03월 2주"   # next Sunday -> week 2


def test_partial_first_week_midweek_month_start():
    # 2026-04-01 is a Wednesday -> Apr 1-4 is the partial week 1
    assert w("2026-04-01")["Week"] == "2026 04월 1주"
    assert w("2026-04-04")["Week"] == "2026 04월 1주"   # Sat
    assert w("2026-04-05")["Week"] == "2026 04월 2주"   # Sun -> week 2


def test_month_boundary_splits():
    # consecutive days across a month boundary land in different buckets
    assert w("2026-04-30")["Week"] == "2026 04월 5주"
    assert w("2026-05-01")["Week"] == "2026 05월 1주"
    assert w("2026-04-30")["Month"] != w("2026-05-01")["Month"]


def test_year_rollover_and_zero_padding():
    assert w("2026-12-31") == {"Year": "2026", "Month": "2026 12월", "Week": "2026 12월 5주"}
    assert w("2027-01-01")["Year"] == "2027"
    # zero-padded month -> plain string sort is chronological (4 < 10)
    assert w("2026-04-08")["Month"] < w("2026-10-08")["Month"]
