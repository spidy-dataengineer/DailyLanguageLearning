"""Daily bilingual language-learning routine: Notion (REST) + Discord.

Modes:
  python daily_notion.py init <parent_page_id>        # create the 3 databases, print their IDs
  python daily_notion.py fetch <en|zh>                # gather raw material -> JSON on stdout
  python daily_notion.py write <en_items.json> <zh_items.json>   # create rows + notify

Python only does I/O (gather + write). The /schedule routine's own Claude reasoning
turns the fetched raw material into the day's items (see routine_prompt.md).
English and Chinese are kept in two separate databases.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import re
import sys

import requests
from dotenv import load_dotenv
from notion_client import Client
from notion_client.helpers import collect_paginated_api

import sources

load_dotenv()

STYLES = ["everyday", "business", "advanced-nuance"]
EN_SOURCES = ["BBC", "Luke's", "Merriam-Webster", "Tatoeba", "Instagram", "YouTube"]
ZH_SOURCES = ["HSK", "Tatoeba", "Instagram", "YouTube"]
TARGETS = {"en": 10, "zh": 10}  # new items written per day, per language
SIM_THRESHOLD = 0.85
MAX_HSK_LEVEL = 6
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}  # Leitner box -> days until next review


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


def _client() -> Client:
    return Client(auth=os.environ["NOTION_TOKEN"])


# --- similarity / dedup ------------------------------------------------------

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s一-鿿]", re.UNICODE)


def norm(s: str) -> str:
    s = _PUNCT.sub("", (s or "").strip().lower())
    return _WS.sub(" ", s).strip()


def similar(a: str, b: str, threshold: float = SIM_THRESHOLD) -> bool:
    """Conservative string-similarity safety net: catches exact repeats, case/punctuation
    variants, whole-phrase containment, reordering, and >=threshold string similarity.

    It deliberately does NOT try to catch morphological inflections (take off / taking off)
    or semantic synonyms -- a string metric can't do that without false positives
    (e.g. affect/effect). Those are the routine-Claude's job, which is given the full
    avoid-list and told to skip morphologically/semantically similar expressions."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # whole-word phrase containment (e.g. "give up" vs "give up on"); skip ultra-short
    short, long = sorted([na, nb], key=len)
    if len(short) >= 4 and re.search(rf"\b{re.escape(short)}\b", long):
        return True
    # high token overlap (same content words, reordered)
    ta, tb = set(na.split()), set(nb.split())
    if len(ta) > 1 and len(tb) > 1 and len(ta & tb) / len(ta | tb) >= 0.8:
        return True
    return difflib.SequenceMatcher(None, na, nb).ratio() >= threshold


def similar_to_any(cand: str, existing, threshold: float = SIM_THRESHOLD) -> bool:
    return any(similar(cand, e, threshold) for e in existing)


# --- Notion helpers ----------------------------------------------------------

_ds_cache: dict[str, str] = {}


def data_source_id(notion: Client, db_id: str) -> str:
    if db_id not in _ds_cache:
        db = notion.databases.retrieve(database_id=db_id)
        ds_list = db.get("data_sources") or []
        if not ds_list:
            raise SystemExit(f"database {db_id} has no data sources")
        _ds_cache[db_id] = ds_list[0]["id"]
    return _ds_cache[db_id]


def _plain(prop) -> str:
    if not prop:
        return ""
    kind = prop.get("type")
    if kind in ("title", "rich_text"):
        return "".join(t.get("plain_text", "") for t in prop.get(kind, []))
    return ""


def _select_name(prop) -> str:
    if prop and prop.get("type") == "select" and prop.get("select"):
        return prop["select"]["name"]
    return ""


def _rich(text: str):
    return [{"type": "text", "text": {"content": (text or "")[:1900]}}] if text else []


def existing_rows(notion: Client, db_id: str):
    ds = data_source_id(notion, db_id)
    rows = collect_paginated_api(notion.data_sources.query, data_source_id=ds)
    return [{"expression": _plain(r.get("properties", {}).get("Expression")),
             "level": _select_name(r.get("properties", {}).get("Level"))} for r in rows]


def inbox_unprocessed(notion: Client, language: str):
    ds = data_source_id(notion, os.environ["NOTION_DB_ID_INBOX"])
    flt = {"and": [
        {"property": "Processed", "checkbox": {"equals": False}},
        {"property": "Language", "select": {"equals": language}},
    ]}
    rows = collect_paginated_api(notion.data_sources.query, data_source_id=ds, filter=flt)
    out = []
    for r in rows:
        p = r.get("properties", {})
        out.append({
            "inbox_page_id": r["id"],
            "link": (p.get("Link") or {}).get("url") or "",
            "raw_text": _plain(p.get("Raw text")),
            "note": _plain(p.get("Note")),
        })
    return out


def hsk_candidates(existing_zh, n: int = 8):
    """Walk HSK levels low->high, return (level, next unused words) for progression."""
    covered_norm = {norm(r["expression"]) for r in existing_zh}
    covered_raw = [r["expression"] for r in existing_zh]
    for level in range(1, MAX_HSK_LEVEL + 1):
        unused = [w for w in sources.hsk_level_words(level)
                  if w["simplified"]
                  and norm(w["simplified"]) not in covered_norm
                  and not similar_to_any(w["simplified"], covered_raw)]
        if unused:
            return level, unused[:n]
    return MAX_HSK_LEVEL, []


# --- modes -------------------------------------------------------------------

def fetch(lang: str) -> None:
    notion = _client()
    today = dt.date.today().isoformat()
    if lang == "en":
        rows = existing_rows(notion, os.environ["NOTION_DB_ID_EN"])
        out = {
            "language": "en", "today": today, "target_count": TARGETS["en"],
            "level": "EN-advanced", "styles": STYLES,
            "avoid": sorted({r["expression"] for r in rows if r["expression"]}),
            "candidates": {
                "merriam_webster": sources.mw_word_of_the_day(),
                "bbc": sources.bbc_six_minute(),
                "lukes": sources.lukes_english(),
                "tatoeba": sources.tatoeba_samples("eng", n=12),
                "inbox": inbox_unprocessed(notion, "English"),
            },
        }
    elif lang == "zh":
        rows = existing_rows(notion, os.environ["NOTION_DB_ID_ZH"])
        level, hsk = hsk_candidates(rows, n=TARGETS["zh"] * 2)
        out = {
            "language": "zh", "today": today, "target_count": TARGETS["zh"],
            "current_hsk_level": level, "styles": STYLES,
            "avoid": sorted({r["expression"] for r in rows if r["expression"]}),
            "candidates": {
                "hsk": hsk,
                "tatoeba": sources.tatoeba_samples("cmn", contains=[w["simplified"] for w in hsk], n=12),
                "inbox": inbox_unprocessed(notion, "Chinese"),
            },
        }
    else:
        raise SystemExit("fetch arg must be 'en' or 'zh'")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _properties(item: dict, lang: str) -> dict:
    props = {
        "Expression": {"title": _rich(item.get("expression"))},
        "Meaning (KO)": {"rich_text": _rich(item.get("meaning_ko"))},
        "Example": {"rich_text": _rich(item.get("example"))},
        "Example (KO)": {"rich_text": _rich(item.get("example_ko"))},
        "Pronunciation": {"rich_text": _rich(item.get("pronunciation"))},
        "Usage note": {"rich_text": _rich(item.get("usage_note"))},
        "Date": {"date": {"start": dt.date.today().isoformat()}},
    }
    if item.get("style") in STYLES:
        props["Style"] = {"select": {"name": item["style"]}}
    level = item.get("level") or ("EN-advanced" if lang == "en" else "")
    if level:
        props["Level"] = {"select": {"name": level}}
    if item.get("source"):
        props["Source"] = {"select": {"name": item["source"]}}
    if item.get("source_url"):
        props["Source URL"] = {"url": item["source_url"]}
    props["Box"] = {"number": 1}  # new cards enter SRS at box 1, due tomorrow
    props["Next review"] = {"date": {"start": (dt.date.today() + dt.timedelta(days=1)).isoformat()}}
    return props


def _icon(lang: str) -> dict:
    return {"type": "emoji", "emoji": "🇬🇧" if lang == "en" else "🇨🇳"}


def _para(text: str, emoji: str = "") -> dict:
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich((f"{emoji} " if emoji else "") + (text or ""))}}


def _callout(text: str, emoji: str) -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"icon": {"type": "emoji", "emoji": emoji}, "rich_text": _rich(text)}}


def _page_body(item: dict) -> list:
    """Flashcard layout: example on top, meaning hidden in a toggle (active recall)."""
    blocks = []
    if item.get("example"):
        blocks.append(_callout(item["example"], "💬"))
    answer = []
    if item.get("meaning_ko"):
        answer.append(_para(item["meaning_ko"]))
    if item.get("example_ko"):
        answer.append(_para("→ " + item["example_ko"]))
    blocks.append({"object": "block", "type": "toggle",
                   "toggle": {"rich_text": _rich("👀 뜻 보기"), "children": answer or [_para("—")]}})
    if item.get("pronunciation"):
        blocks.append(_para(item["pronunciation"], "🔊"))
    if item.get("usage_note"):
        blocks.append(_callout(item["usage_note"], "📝"))
    src, url = item.get("source") or "", item.get("source_url") or ""
    if url:
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": "🔗 " + (src or url), "link": {"url": url}}}]}})
    elif src:
        blocks.append(_para(src, "🔗"))
    return blocks


def _practice_body(sentences: list) -> list:
    """A daily-practice page: each sentence visible (zh + pinyin), Korean hidden in a toggle."""
    blocks = [_callout("오늘 배운 표현으로 만든 문장 — 읽고 뜻을 떠올려본 뒤 펼쳐 확인하세요.", "✍️")]
    for s in sentences:
        head = s.get("zh", "")
        if s.get("pinyin"):
            head = f"{head}  ({s['pinyin']})"
        blocks.append({"object": "block", "type": "toggle",
                       "toggle": {"rich_text": _rich(head), "children": [_para(s.get("ko") or "—")]}})
    return blocks


def _write_practice(notion: Client, ds: str, sentences: list) -> None:
    if not sentences:
        return
    today = dt.date.today().isoformat()
    notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": ds},
        properties={"Expression": {"title": _rich(f"📝 오늘의 연습 · {today}")},
                    "Date": {"date": {"start": today}}},
        icon={"type": "emoji", "emoji": "✍️"},
        children=_practice_body(sentences))


def write(en_file, zh_file) -> None:
    notion = _client()
    written = {"en": [], "zh": []}
    skipped = []
    processed_inbox = []
    for lang, path, db_env in [("en", en_file, "NOTION_DB_ID_EN"), ("zh", zh_file, "NOTION_DB_ID_ZH")]:
        if not path or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        db_id = os.environ[db_env]
        ds = data_source_id(notion, db_id)
        seen = [r["expression"] for r in existing_rows(notion, db_id) if r["expression"]]
        for item in items:
            if item.get("type") == "practice":  # daily "use the day's words" sentences
                _write_practice(notion, ds, item.get("sentences") or [])
                continue
            expr = (item.get("expression") or "").strip()
            if not expr:
                continue
            if similar_to_any(expr, seen):  # write-time dedup safety net
                skipped.append(f"{lang}: {expr}")
                continue
            notion.pages.create(parent={"type": "data_source_id", "data_source_id": ds},
                                properties=_properties(item, lang),
                                icon=_icon(lang),
                                children=_page_body(item))
            seen.append(expr)
            written[lang].append(item)
            if item.get("inbox_page_id"):
                processed_inbox.append(item["inbox_page_id"])
    for pid in set(processed_inbox):
        notion.pages.update(page_id=pid, properties={"Processed": {"checkbox": True}})
    notify_discord(written)
    if skipped:
        _log(f"skipped {len(skipped)} similar/duplicate: {skipped}")
    print(json.dumps({"written_en": len(written["en"]), "written_zh": len(written["zh"]),
                      "skipped": skipped}, ensure_ascii=False, indent=2))


def notify_discord(written: dict) -> None:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        _log("no DISCORD_WEBHOOK_URL; skipping notification")
        return
    if not (written.get("en") or written.get("zh")):
        _log("nothing written; skipping notification")
        return
    lines = [f"📚 **오늘의 표현** ({dt.date.today().isoformat()})"]
    if written["en"]:
        lines += ["", "🇬🇧 **English**"]
        lines += [f"• **{i.get('expression','')}** — {i.get('meaning_ko','')}" for i in written["en"]]
    if written["zh"]:
        lines += ["", "🇨🇳 **中文**"]
        lines += [f"• **{i.get('expression','')}** ({i.get('pronunciation','')}) — {i.get('meaning_ko','')}"
                  for i in written["zh"]]
    for label, env in [("English", "NOTION_DB_ID_EN"), ("中文", "NOTION_DB_ID_ZH")]:
        db = os.environ.get(env, "")
        if db:
            lines.append(f"📖 {label}: https://www.notion.so/{db.replace('-', '')}")
    try:
        requests.post(url, json={"content": "\n".join(lines)[:1990]}, timeout=20).raise_for_status()
    except requests.RequestException as e:
        _log(f"Discord notify failed: {e}")


# --- SRS review (spaced repetition) ------------------------------------------

def _due_date(prop):
    d = (prop or {}).get("date")
    return d.get("start") if d else None


def due_rows(notion: Client, db_id: str) -> list:
    """Vocab rows due for review (Next review empty or <= today). Skips practice rows."""
    ds = data_source_id(notion, db_id)
    today = dt.date.today().isoformat()
    out = []
    for r in collect_paginated_api(notion.data_sources.query, data_source_id=ds):
        p = r.get("properties", {})
        expr, meaning = _plain(p.get("Expression")), _plain(p.get("Meaning (KO)"))
        if not expr or not meaning:  # skip practice / non-vocab rows
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
    today = dt.date.today()
    notion.pages.update(page_id=page_id, properties={
        "Box": {"number": new_box},
        "Next review": {"date": {"start": (today + dt.timedelta(days=INTERVALS[new_box])).isoformat()}},
        "Last reviewed": {"date": {"start": today.isoformat()}},
        "Recall": {"select": None},  # clear for the next cycle
    })


def review() -> None:
    notion = _client()
    due = {"en": [], "zh": []}
    for lang, env in (("en", "NOTION_DB_ID_EN"), ("zh", "NOTION_DB_ID_ZH")):
        for row in due_rows(notion, os.environ[env]):
            reschedule(notion, row["page_id"], row["box"], row["recall"])
            due[lang].append(row)
    notify_review(due)
    print(json.dumps({"due_en": len(due["en"]), "due_zh": len(due["zh"])}, ensure_ascii=False))


def notify_review(due: dict) -> None:
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    n = len(due["en"]) + len(due["zh"])
    if not url or n == 0:
        _log("review: nothing due or no webhook; skipping ping")
        return
    lines = [f"🧠 **복습 ({dt.date.today().isoformat()}) — {n}개** · 뜻은 ||가림||, 기억했으면 Notion에서 Recall 표시"]
    for lang, flag in (("en", "🇬🇧 English"), ("zh", "🇨🇳 中文")):
        if due[lang]:
            lines += ["", f"**{flag}**"]
            lines += [f"• **{r['expression']}** — ||{r['meaning_ko']}||" for r in due[lang]]
    try:
        requests.post(url, json={"content": "\n".join(lines)[:1990]}, timeout=20).raise_for_status()
    except requests.RequestException as e:
        _log(f"review ping failed: {e}")


# --- init --------------------------------------------------------------------

_SRS_PROPS = {
    "Box": {"number": {"format": "number"}},
    "Next review": {"date": {}},
    "Recall": {"select": {"options": [{"name": "Got it"}, {"name": "Forgot"}]}},
    "Last reviewed": {"date": {}},
}

_EXPR_SCHEMA_BASE = {
    "Expression": {"title": {}},
    "Meaning (KO)": {"rich_text": {}},
    "Example": {"rich_text": {}},
    "Example (KO)": {"rich_text": {}},
    "Pronunciation": {"rich_text": {}},
    "Style": {"select": {"options": [{"name": s} for s in STYLES]}},
    "Usage note": {"rich_text": {}},
    "Source URL": {"url": {}},
    "Date": {"date": {}},
    "Audio": {"url": {}},
    **_SRS_PROPS,
}

_INBOX_SCHEMA = {
    "Item": {"title": {}},
    "Link": {"url": {}},
    "Raw text": {"rich_text": {}},
    "Language": {"select": {"options": [{"name": "English"}, {"name": "Chinese"}]}},
    "Note": {"rich_text": {}},
    "Processed": {"checkbox": {}},
    "Added": {"date": {}},
}


def _expr_schema(lang: str) -> dict:
    schema = dict(_EXPR_SCHEMA_BASE)
    if lang == "en":
        schema["Level"] = {"select": {"options": [{"name": "EN-advanced"}]}}
        schema["Source"] = {"select": {"options": [{"name": s} for s in EN_SOURCES]}}
    else:
        schema["Level"] = {"select": {"options": [{"name": f"HSK{i}"} for i in range(1, MAX_HSK_LEVEL + 1)]}}
        schema["Source"] = {"select": {"options": [{"name": s} for s in ZH_SOURCES]}}
    return schema


def _create_db(notion: Client, parent_page_id: str, title: str, schema: dict) -> str:
    db = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": title}}],
        initial_data_source={"properties": schema},
    )
    return db["id"]


def init(en_page_id: str, zh_page_id: str, inbox_page_id: str | None = None) -> None:
    notion = _client()
    inbox_page_id = inbox_page_id or en_page_id
    for pid in {en_page_id, zh_page_id, inbox_page_id}:  # fail before creating anything if a page isn't shared
        try:
            notion.pages.retrieve(page_id=pid)
        except Exception as e:
            raise SystemExit(f"Cannot access page {pid}: add the integration via '•••' > Connections.\n  {e}")
    en = _create_db(notion, en_page_id, "English Expressions", _expr_schema("en"))
    zh = _create_db(notion, zh_page_id, "Chinese Expressions", _expr_schema("zh"))
    inbox = _create_db(notion, inbox_page_id, "Language Inbox", _INBOX_SCHEMA)
    print("# Add these to .env / your routine env vars:")
    print(f"NOTION_DB_ID_EN={en}")
    print(f"NOTION_DB_ID_ZH={zh}")
    print(f"NOTION_DB_ID_INBOX={inbox}")


def migrate() -> None:
    """Add SRS properties to the existing English + Chinese databases (idempotent)."""
    notion = _client()
    for env in ("NOTION_DB_ID_EN", "NOTION_DB_ID_ZH"):
        notion.data_sources.update(data_source_id=data_source_id(notion, os.environ[env]),
                                   properties=_SRS_PROPS)
        print(f"migrated {env}: SRS properties ensured")


def main(argv) -> None:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp949; force UTF-8
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2:
        raise SystemExit(__doc__)
    cmd = argv[1]
    if cmd == "init":
        if len(argv) < 4:
            raise SystemExit("usage: daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]")
        init(argv[2], argv[3], argv[4] if len(argv) > 4 else None)
    elif cmd == "fetch":
        if len(argv) < 3:
            raise SystemExit("usage: daily_notion.py fetch <en|zh>")
        fetch(argv[2])
    elif cmd == "migrate":
        migrate()
    elif cmd == "review":
        review()
    elif cmd == "write":
        write(argv[2] if len(argv) > 2 else None, argv[3] if len(argv) > 3 else None)
    else:
        raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main(sys.argv)
