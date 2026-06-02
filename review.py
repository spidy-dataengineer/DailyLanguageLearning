"""SRS review (spaced repetition): find due cards, reschedule on the Leitner curve, ping Discord."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from notion_client import Client
from notion_client.helpers import collect_paginated_api

from constants import INTERVALS, kst_today
from notion_io import _client, _due_date, _plain, _select_name, data_source_id
from notify import notify_review
from stats import compute_stats


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


def due_rows(notion: Client, db_id: str) -> list:
    """Vocab rows due for review (Next review empty or <= today). Skips practice rows."""
    ds = data_source_id(notion, db_id)
    today = kst_today().isoformat()
    out = []
    for r in collect_paginated_api(notion.data_sources.query, data_source_id=ds):
        p = r.get("properties", {})
        expr, meaning = _plain(p.get("Expression")), _plain(p.get("Meaning (KO)"))
        if not expr or not meaning:
            continue
        nr = _due_date(p.get("Next review"))
        if nr is not None and nr > today:
            continue
        out.append({"page_id": r["id"], "expression": expr, "meaning_ko": meaning,
                    "box": (p.get("Box") or {}).get("number") or 1,
                    "recall": _select_name(p.get("Recall"))})
    return out


def reschedule(notion: Client, page_id: str, box: int, recall: str) -> None:
    new_box = min(box + 1, 5) if recall == "Got it" else 1 if recall == "Forgot" else box
    today = kst_today()
    notion.pages.update(page_id=page_id, properties={
        "Box": {"number": new_box},
        "Next review": {"date": {"start": (today + dt.timedelta(days=INTERVALS[new_box])).isoformat()}},
        "Last reviewed": {"date": {"start": today.isoformat()}},
        "Recall": {"select": None},
    })


def review() -> None:
    notion = _client()
    due = {"en": [], "zh": []}
    for lang, env in (("en", "NOTION_DB_ID_EN"), ("zh", "NOTION_DB_ID_ZH")):
        for row in due_rows(notion, os.environ[env]):
            reschedule(notion, row["page_id"], row["box"], row["recall"])
            due[lang].append(row)
    notify_review(due, compute_stats(notion))
    print(json.dumps({"due_en": len(due["en"]), "due_zh": len(due["zh"])}, ensure_ascii=False))
