"""SRS review (spaced repetition): find due cards, reschedule on the Leitner curve, ping Discord."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from notion_client import Client
from notion_client.helpers import collect_paginated_api

from constants import INTERVALS, REVIEW_CAP, kst_today
from notion.notion_io import _client, _due_date, _plain, _select_name, data_source_id
from notify.notify import notify_review
from srs.stats import compute_stats


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
                    "recall": _select_name(p.get("Recall")),
                    "next": nr, "created": _due_date(p.get("Date"))})
    return out


def pick(rows: list, cap: int) -> list:
    """Today's review slice: every card the user marked (a Recall must never wait in the queue) plus the
    longest-waiting unmarked cards, up to `cap` in total. The rest stay due and come first tomorrow."""
    marked = [r for r in rows if r["recall"]]
    waiting = sorted((r for r in rows if not r["recall"]), key=lambda r: (r["next"] or "", r["created"] or ""))
    return marked + waiting[:max(cap - len(marked), 0)]


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
    due, total = {"en": [], "zh": []}, {}
    for lang, env in (("en", "NOTION_DB_ID_EN"), ("zh", "NOTION_DB_ID_ZH")):
        rows = due_rows(notion, os.environ[env])
        total[lang] = len(rows)
        for row in pick(rows, REVIEW_CAP):
            reschedule(notion, row["page_id"], row["box"], row["recall"])
            due[lang].append(row)
    left = total["en"] + total["zh"] - len(due["en"]) - len(due["zh"])
    notify_review(due, compute_stats(notion), left)
    print(json.dumps({"due_en": total["en"], "due_zh": total["zh"],
                      "reviewed_en": len(due["en"]), "reviewed_zh": len(due["zh"])}, ensure_ascii=False))
