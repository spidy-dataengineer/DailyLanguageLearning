"""The quiz app's card database (Supabase), the cards' source since 2026-11-10.

New cards go here first; the Notion page made after it is a backup, linked in `card_backups`. The app repo's
daily job keeps Notion following the database (language-quiz `docs/db-source-plan.md`).

The cloud routine sends no key: its environment holds the secret key as a network secret and adds the `apikey`
header on the way out, so the run never sees it. A local run reads SUPABASE_SERVICE_KEY from `.env` instead.
"""
from __future__ import annotations

import datetime as dt
import os

import requests

from constants import STYLES, SUPABASE_URL

PAGE = 1000
TIMEOUT = 30


def _headers(prefer: str | None = None) -> dict:
    h = {"Content-Type": "application/json"}
    if os.environ.get("SUPABASE_SERVICE_KEY"):
        h["apikey"] = os.environ["SUPABASE_SERVICE_KEY"]
    if prefer:
        h["Prefer"] = prefer
    return h


def _url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


def _get_all(table: str, params: dict) -> list[dict]:
    rows, offset = [], 0
    while True:
        r = requests.get(_url(table), headers=_headers(), timeout=TIMEOUT,
                         params={**params, "limit": PAGE, "offset": offset})
        r.raise_for_status()
        page = r.json()
        rows += page
        if len(page) < PAGE:
            return rows
        offset += PAGE


def reachable() -> dict:
    """One small read: whether the database answers and accepts the key, without printing anything secret."""
    r = requests.get(_url("cards"), headers=_headers(), params={"select": "id", "limit": 1}, timeout=TIMEOUT)
    return {"ok": r.ok, "status": r.status_code}


def saved_rows(lang: str) -> list[dict]:
    """Every card of the language still in use, in the shape dedup and the candidate lists read."""
    rows = _get_all("cards", {"select": "expression,level,origin,source_url", "lang": f"eq.{lang}",
                              "archived_at": "is.null", "order": "id"})
    return [{"expression": r["expression"], "level": r["level"], "source": r["origin"] or "",
             "source_url": r["source_url"]} for r in rows]


def card_row(item: dict, lang: str, options: list | None, audio_url: str | None, today: dt.date) -> dict:
    """A card as the `cards` table holds it. `source` (the name learners see) is made from `origin` by the
    table's trigger, and `id` by its default."""
    return {
        "lang": lang,
        "expression": (item.get("expression") or "").strip(),
        "meaning_ko": item.get("meaning_ko") or "",
        "example": item.get("example") or "",
        "example_ko": item.get("example_ko") or "",
        "example2": item.get("example2") or "",
        "example2_ko": item.get("example2_ko") or "",
        "pronunciation": item.get("pronunciation") or "",
        "usage_note": item.get("usage_note") or "",
        "style": item.get("style") if item.get("style") in STYLES else "",
        "level": item.get("level") or "",
        "origin": item.get("source") or "",
        "source_url": item.get("source_url"),
        "audio_url": audio_url,
        "added_on": today.isoformat(),
        "options": options,
    }


def insert_card(row: dict) -> str:
    """Adds the card and returns the id the database gave it."""
    r = requests.post(_url("cards"), headers=_headers("return=representation"), params={"select": "id"},
                      json=row, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()[0]["id"]


def record_backup(card_id: str, notion_page_id: str) -> None:
    r = requests.post(_url("card_backups"), headers=_headers("return=minimal"), timeout=TIMEOUT, json={
        "card_id": card_id, "notion_page_id": notion_page_id,
        "backed_up_at": dt.datetime.now(dt.timezone.utc).isoformat()})
    r.raise_for_status()


def missing_options(lang: str, n: int) -> list[dict]:
    """Cards with no written wrong options yet, newest first, with what writing them needs."""
    r = requests.get(_url("cards"), headers=_headers(), timeout=TIMEOUT, params={
        "select": "id,expression,meaning_ko,example,example_ko,style,level", "lang": f"eq.{lang}",
        "options": "is.null", "archived_at": "is.null", "order": "added_on.desc.nullslast,id", "limit": n})
    r.raise_for_status()
    return r.json()


def cards_by_id(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    r = requests.get(_url("cards"), headers=_headers(), timeout=TIMEOUT, params={
        "select": "id,expression,meaning_ko,example", "id": f"in.({','.join(ids)})"})
    r.raise_for_status()
    return {c["id"]: c for c in r.json()}


def set_options(card_id: str, expression: str, options: list) -> bool:
    """Writes the options if the card still has that expression; False when it changed meanwhile."""
    r = requests.patch(_url("cards"), headers=_headers("return=representation"), timeout=TIMEOUT,
                       params={"id": f"eq.{card_id}", "expression": f"eq.{expression}", "select": "id"},
                       json={"options": options})
    r.raise_for_status()
    return bool(r.json())
