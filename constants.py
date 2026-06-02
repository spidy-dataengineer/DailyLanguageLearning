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
