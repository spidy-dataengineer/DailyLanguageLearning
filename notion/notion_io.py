"""Notion I/O — Notion API client, schema/init, page layout, audio URLs, fetch + write modes.

Everything that talks to Notion's REST API lives here. See `docs/notion.md` for the data model
(properties, schemas) and `docs/dedup.md` for how this collaborates with `dedup.py`.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import os
import re
import sys
import unicodedata
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from notion_client import Client
from notion_client.helpers import collect_paginated_api

from content import sources
from constants import EN_SOURCES, MAX_HSK_LEVEL, STYLES, TARGETS, ZH_SOURCES, kst_today, period_labels
from content.dedup import similar_to_any
from notify.notify import notify_write

load_dotenv()


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


def _client() -> Client:
    return Client(auth=os.environ["NOTION_TOKEN"])


# --- Notion property helpers -------------------------------------------------

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


def _due_date(prop):
    d = (prop or {}).get("date")
    return d.get("start") if d else None


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


# --- fetch mode --------------------------------------------------------------

def fetch(lang: str) -> None:
    from content.dedup import hsk_candidates  # local to avoid touching dedup at module load
    notion = _client()
    today = kst_today().isoformat()
    if lang == "en":
        rows = existing_rows(notion, os.environ["NOTION_DB_ID_EN"])
        out = {
            "language": "en", "today": today, "target_count": TARGETS["en"],
            "level": "EN-advanced", "styles": STYLES,
            "avoid": sorted({r["expression"] for r in rows if r["expression"]}),
            "candidates": {
                "merriam_webster": sources.mw_word_of_the_day(),
                "bbc": sources.bbc_six_minute(),
                "bbc_phrases": sources.bbc_the_english_we_speak(),
                "youtube": sources.youtube_channels(),
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


# --- audio URLs (pronunciation) ----------------------------------------------

def youglish_url(expr: str, lang: str) -> str:
    """Pronunciation as a YouGlish search link — no file upload, hosting, or API key."""
    return f"https://youglish.com/pronounce/{quote(expr or '')}/{'chinese' if lang == 'zh' else 'english'}"


_AUDIO_CMN = "https://cdn.jsdelivr.net/gh/hugolpz/audio-cmn@master/64k/hsk/cmn-{}.mp3"


@functools.lru_cache(maxsize=None)
def zh_audio_url(word: str) -> str | None:
    """Native-speaker recording from audio-cmn (CC BY-SA) if it covers this word, else None.
    A 200 means the mp3 exists; 403/404 (word not in the set) or a network error -> None, so the
    caller falls back to a YouGlish link. Covers ~80% of single HSK words, fewer multi-char phrases."""
    if not word:
        return None
    url = _AUDIO_CMN.format(quote(word))
    try:
        ok = requests.head(url, timeout=8, allow_redirects=True).status_code == 200
    except requests.RequestException:
        return None
    return url if ok else None


def _audio_block(url: str) -> dict:
    return {"object": "block", "type": "audio", "audio": {"type": "external", "external": {"url": url}}}


_WIKI_UA = {"User-Agent": "DailyLanguageLearning/1.0 (personal language-study project)"}
_COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_AUDIO_EXT = (".ogg", ".oga", ".wav", ".mp3")


def _ascii_pinyin(s: str) -> str:
    """Tone- and separator-free ascii pinyin for matching ('nǐ hǎo · 안녕' -> 'nihao')."""
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if c.isascii() and c.isalpha()).lower()


def _pinyin_matches(want: str, title: str) -> bool:
    name = re.sub(r"\.(ogg|oga|wav|mp3)$", "", title.split(":", 1)[-1], flags=re.I)
    name = re.sub(r"^\s*zh[-\s_]*", "", name, flags=re.I)
    got = _ascii_pinyin(name)
    return bool(want) and (want == got or (len(want) >= 4 and (want in got or got in want)))


@functools.lru_cache(maxsize=None)
def _commons_audio_url(word: str, pinyin: str) -> str | None:
    """A Wikimedia Commons recording whose filename pinyin matches `pinyin`, so we never attach the
    wrong word's audio. Requires a pinyin to verify against -> returns None without one (safe skip).
    Wikimedia requires a User-Agent and discourages hotlinking; acceptable for a last-resort fallback."""
    want = _ascii_pinyin(pinyin)
    if not word or len(want) < 2:
        return None
    try:
        hits = requests.get(_COMMONS_API, headers=_WIKI_UA, timeout=10, params={
            "action": "query", "list": "search", "srnamespace": "6", "srlimit": "5",
            "format": "json", "srsearch": f"zh pronunciation {word}"}).json()
        titles = [h["title"] for h in hits.get("query", {}).get("search", [])
                  if h["title"].lower().endswith(_AUDIO_EXT) and _pinyin_matches(want, h["title"])]
        if not titles:
            return None
        info = requests.get(_COMMONS_API, headers=_WIKI_UA, timeout=10, params={
            "action": "query", "titles": titles[0], "prop": "imageinfo",
            "iiprop": "url", "format": "json", "redirects": "1"}).json()
        page = next(iter(info["query"]["pages"].values()))
        return page.get("imageinfo", [{}])[0].get("url")
    except (requests.RequestException, ValueError, KeyError, StopIteration):
        return None


def native_audio_url(expr: str, pinyin: str) -> str | None:
    """Native ZH recording: audio-cmn (instant, ~80% single words) -> Wikimedia Commons (pinyin-verified)."""
    return zh_audio_url(expr) or _commons_audio_url(expr, pinyin)


def _audio_credit(url: str) -> tuple[str, str]:
    if "wikimedia.org" in url:
        return "🔊 원어민 발음: Wikimedia Commons (CC BY-SA)", "https://commons.wikimedia.org"
    return "🔊 원어민 발음: audio-cmn (CC BY-SA)", "https://github.com/hugolpz/audio-cmn"


# --- page layout (flashcard / practice rendering) ----------------------------

def _properties(item: dict, lang: str) -> dict:
    props = {
        "Expression": {"title": _rich(item.get("expression"))},
        "Meaning (KO)": {"rich_text": _rich(item.get("meaning_ko"))},
        "Example": {"rich_text": _rich(item.get("example"))},
        "Example (KO)": {"rich_text": _rich(item.get("example_ko"))},
        "Example 2": {"rich_text": _rich(item.get("example2"))},
        "Example 2 (KO)": {"rich_text": _rich(item.get("example2_ko"))},
        "Pronunciation": {"rich_text": _rich(item.get("pronunciation"))},
        "Usage note": {"rich_text": _rich(item.get("usage_note"))},
        "Date": {"date": {"start": kst_today().isoformat()}},
    }
    for name, val in period_labels(kst_today()).items():
        props[name] = {"select": {"name": val}}
    if item.get("style") in STYLES:
        props["Style"] = {"select": {"name": item["style"]}}
    level = item.get("level") or ("EN-advanced" if lang == "en" else "")
    if level:
        props["Level"] = {"select": {"name": level}}
    if item.get("source"):
        props["Source"] = {"select": {"name": item["source"]}}
    if item.get("source_url"):
        props["Source URL"] = {"url": item["source_url"]}
    if lang == "zh":
        expr = item.get("expression")
        props["Audio"] = {"url": native_audio_url(expr, item.get("pronunciation")) or youglish_url(expr, lang)}
    props["Box"] = {"number": 1}
    props["Next review"] = {"date": {"start": (kst_today() + dt.timedelta(days=1)).isoformat()}}
    return props


def _icon(lang: str) -> dict:
    return {"type": "emoji", "emoji": "🇬🇧" if lang == "en" else "🇨🇳"}


def _para(text: str, emoji: str = "") -> dict:
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich((f"{emoji} " if emoji else "") + (text or ""))}}


def _callout(text: str, emoji: str) -> dict:
    return {"object": "block", "type": "callout",
            "callout": {"icon": {"type": "emoji", "emoji": emoji}, "rich_text": _rich(text)}}


def _toggle(label: str, children: list) -> dict:
    return {"object": "block", "type": "toggle",
            "toggle": {"rich_text": _rich(label), "children": children}}


_BLANK = "____"


def cloze(example: str, expression: str) -> str:
    """Hide the expression inside the example with a blank for active recall. Case-insensitive;
    returns the example unchanged (fail-soft) when the expression isn't found verbatim."""
    if not example or not expression:
        return example or ""
    blanked, n = re.subn(re.escape(expression.strip()), _BLANK, example, flags=re.IGNORECASE)
    return blanked if n else example


def _page_body(item: dict, lang: str) -> list:
    """Flashcard layout: a cloze example on top (active recall), the full answer hidden in a
    '뜻 보기' toggle, plus a reverse toggle (meaning shown -> expression hidden)."""
    blocks = []
    example = item.get("example") or ""
    blanked = cloze(example, item.get("expression"))
    if example:
        blocks.append(_callout(blanked, "💬"))
    answer = []
    if item.get("meaning_ko"):
        answer.append(_para(item["meaning_ko"]))
    if blanked != example:
        answer.append(_para(example))
    if item.get("example_ko"):
        answer.append(_para("→ " + item["example_ko"]))
    if item.get("example2"):
        answer.append(_para("〔다른 상황〕 " + item["example2"]))
        if item.get("example2_ko"):
            answer.append(_para("→ " + item["example2_ko"]))
    blocks.append(_toggle("👀 뜻 보기", answer or [_para("—")]))
    rev_label = "🔄 거꾸로 (뜻→표현)" + (f": {item['meaning_ko']}" if item.get("meaning_ko") else "")
    blocks.append(_toggle(rev_label, [_para(item.get("expression") or "—")]))
    if item.get("pronunciation"):
        blocks.append(_para(item["pronunciation"], "🔊"))
    if lang == "zh":
        expr = item.get("expression")
        native = native_audio_url(expr, item.get("pronunciation"))
        if native:
            blocks.append(_audio_block(native))
            label, link = _audio_credit(native)
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": label, "link": {"url": link}}}]}})
        else:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "🔊 발음 듣기",
                               "link": {"url": youglish_url(expr, lang)}}}]}})
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
    today = kst_today()
    props = {"Expression": {"title": _rich(f"📝 오늘의 연습 · {today.isoformat()}")},
             "Date": {"date": {"start": today.isoformat()}}}
    for name, val in period_labels(today).items():
        props[name] = {"select": {"name": val}}
    notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": ds},
        properties=props,
        icon={"type": "emoji", "emoji": "✍️"},
        children=_practice_body(sentences))


# --- write mode --------------------------------------------------------------

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
            if item.get("type") == "practice":
                _write_practice(notion, ds, item.get("sentences") or [])
                continue
            expr = (item.get("expression") or "").strip()
            if not expr:
                continue
            if similar_to_any(expr, seen):
                skipped.append(f"{lang}: {expr}")
                continue
            notion.pages.create(parent={"type": "data_source_id", "data_source_id": ds},
                                properties=_properties(item, lang),
                                icon=_icon(lang),
                                children=_page_body(item, lang))
            seen.append(expr)
            written[lang].append(item)
            if item.get("inbox_page_id"):
                processed_inbox.append(item["inbox_page_id"])
    for pid in set(processed_inbox):
        notion.pages.update(page_id=pid, properties={"Processed": {"checkbox": True}})
    notify_write(written)
    if skipped:
        _log(f"skipped {len(skipped)} similar/duplicate: {skipped}")
    print(json.dumps({"written_en": len(written["en"]), "written_zh": len(written["zh"]),
                      "skipped": skipped}, ensure_ascii=False, indent=2))


# --- init / migrate ----------------------------------------------------------

_SRS_PROPS = {
    "Box": {"number": {"format": "number"}},
    "Next review": {"date": {}},
    "Recall": {"select": {"options": [{"name": "Got it"}, {"name": "Forgot"}]}},
    "Last reviewed": {"date": {}},
}

_PERIOD_PROPS = {
    "Year": {"select": {}},
    "Month": {"select": {}},
    "Week": {"select": {}},
}

_EXAMPLE2_PROPS = {
    "Example 2": {"rich_text": {}},
    "Example 2 (KO)": {"rich_text": {}},
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
    **_PERIOD_PROPS,
    **_EXAMPLE2_PROPS,
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
    for pid in {en_page_id, zh_page_id, inbox_page_id}:
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
    """Add SRS + calendar-period (Year/Month/Week) + Example 2 properties to the English + Chinese
    databases, then backfill Year/Month/Week on rows that lack them, from each row's Date (idempotent)."""
    notion = _client()
    for env in ("NOTION_DB_ID_EN", "NOTION_DB_ID_ZH"):
        ds = data_source_id(notion, os.environ[env])
        notion.data_sources.update(data_source_id=ds,
                                   properties={**_SRS_PROPS, **_PERIOD_PROPS, **_EXAMPLE2_PROPS})
        backfilled = 0
        for r in collect_paginated_api(notion.data_sources.query, data_source_id=ds):
            p = r.get("properties", {})
            if _select_name(p.get("Week")):
                continue  # period labels already set on a prior migrate
            d = _due_date(p.get("Date"))
            if not d:
                continue
            labels = period_labels(dt.date.fromisoformat(d))
            notion.pages.update(page_id=r["id"],
                                properties={k: {"select": {"name": v}} for k, v in labels.items()})
            backfilled += 1
        print(f"migrated {env}: SRS + period + Example 2 properties ensured, backfilled {backfilled} rows")
