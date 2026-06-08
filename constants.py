"""Shared constants for the daily language-learning routine."""
import datetime as dt

STYLES = ["everyday", "situational", "idiom", "business"]
EN_SOURCES = ["BBC", "Luke's", "Merriam-Webster", "Tatoeba", "Instagram", "YouTube"]
ZH_SOURCES = ["HSK", "Tatoeba", "Instagram", "YouTube"]
TARGETS = {"en": 10, "zh": 10}
SIM_THRESHOLD = 0.85
MAX_HSK_LEVEL = 6
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}

# All "today" stamps use Korea time. The cloud routine runs in UTC, so a plain
# date.today() at the 08:00 KST (23:00 UTC) run resolves to the previous day.
# KST has no DST, so a fixed +9 offset is correct year-round (no tzdata dependency).
KST = dt.timezone(dt.timedelta(hours=9))


def kst_today() -> dt.date:
    return dt.datetime.now(KST).date()


def period_labels(d: dt.date) -> dict[str, str]:
    """Calendar Year / Month / Week-of-month labels for grouping cards in a Notion view.

    Week starts Sunday (Korean wall-calendar convention) and the week containing the 1st of the
    month is week 1. Month is zero-padded so a plain string sort orders the select options
    chronologically ('2026 04월' before '2026 10월'). Derived from a card's Date, so English and
    Chinese cards bucket identically. See docs/notion.md.
    """
    first_dow = (d.replace(day=1).weekday() + 1) % 7  # weekday of the 1st, Sun=0 .. Sat=6
    week = (d.day + first_dow - 1) // 7 + 1
    return {
        "Year": f"{d.year}",
        "Month": f"{d.year} {d.month:02d}월",
        "Week": f"{d.year} {d.month:02d}월 {week}주",
    }
