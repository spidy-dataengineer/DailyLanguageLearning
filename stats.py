"""Read-only aggregates over saved vocab rows: total / due / box distribution / HSK / streak.

Derived entirely from existing Notion rows — no dashboard DB, no extra properties.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from notion_client import Client
from notion_client.helpers import collect_paginated_api

from notion_io import _client, _due_date, _plain, _select_name, data_source_id
from notify import notify_stats


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


def _streak(dates: set, today: dt.date) -> int:
    """Consecutive days (with >=1 card) ending today, or yesterday if nothing is dated today yet."""
    d = today if today.isoformat() in dates else today - dt.timedelta(days=1)
    n = 0
    while d.isoformat() in dates:
        n += 1
        d -= dt.timedelta(days=1)
    return n


def compute_stats(notion: Client) -> dict:
    """Read-only aggregates derived entirely from existing vocab rows — no dashboard DB, no new fields."""
    today = dt.date.today()
    by_lang = {}
    dates: set = set()
    for lang, env in (("en", "NOTION_DB_ID_EN"), ("zh", "NOTION_DB_ID_ZH")):
        ds = data_source_id(notion, os.environ[env])
        total = due = 0
        boxes: dict = {}
        hsk: dict = {}
        for r in collect_paginated_api(notion.data_sources.query, data_source_id=ds):
            p = r.get("properties", {})
            if not _plain(p.get("Expression")) or not _plain(p.get("Meaning (KO)")):
                continue
            total += 1
            box = int((p.get("Box") or {}).get("number") or 1)
            boxes[box] = boxes.get(box, 0) + 1
            nr = _due_date(p.get("Next review"))
            if nr is None or nr <= today.isoformat():
                due += 1
            d = _due_date(p.get("Date"))
            if d:
                dates.add(d)
            lvl = _select_name(p.get("Level"))
            if lang == "zh" and lvl:
                hsk[lvl] = hsk.get(lvl, 0) + 1
        entry = {"total": total, "due": due, "boxes": {str(k): boxes[k] for k in sorted(boxes)}}
        if lang == "zh":
            entry["hsk"] = {k: hsk[k] for k in sorted(hsk)}
        by_lang[lang] = entry
    return {"today": today.isoformat(), "streak": _streak(dates, today),
            "total": by_lang["en"]["total"] + by_lang["zh"]["total"], "by_lang": by_lang}


def stats() -> None:
    notion = _client()
    s = compute_stats(notion)
    notify_stats(s)
    print(json.dumps(s, ensure_ascii=False, indent=2))
