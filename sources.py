"""Seed-content fetchers for the daily language-learning routine.

Each fetcher returns plain data (dict / list / None). Network calls fail soft:
on any error they log to stderr and return an empty result, so one dead source
never breaks the daily run. No Notion access here (that lives in daily_notion.py).
"""
from __future__ import annotations

import os
import random
import sys

import feedparser
import requests
from bs4 import BeautifulSoup

UA = "daily-lang-notion/1.0 (personal language-learning automation)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})
TIMEOUT = 20


def _log(msg: str) -> None:
    print(f"[sources] {msg}", file=sys.stderr)


def _get(url: str):
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        _log(f"GET failed {url}: {e}")
        return None


def _text(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


# --- English -----------------------------------------------------------------

MW_WOTD_RSS = "https://www.merriam-webster.com/wotd/feed/rss2"
BBC_6MIN_RSS = "https://podcasts.files.bbci.co.uk/p02pc9tn.rss"
LUKES_RSS = "https://teacherluke.co.uk/feed/"


def mw_word_of_the_day():
    feed = feedparser.parse(MW_WOTD_RSS)
    if not feed.entries:
        _log("MW WOTD: no entries")
        return None
    e = feed.entries[0]
    return {"word": e.title, "definition": _text(getattr(e, "summary", ""))[:600], "url": e.link}


def bbc_six_minute():
    feed = feedparser.parse(BBC_6MIN_RSS)
    if not feed.entries:
        _log("BBC: no entries")
        return None
    e = feed.entries[0]
    notes = BeautifulSoup(getattr(e, "summary", ""), "html.parser")
    # the episode description links to the full transcript page on bbc.co.uk/learningenglish
    page_url = next((a["href"] for a in notes.find_all("a", href=True)
                     if "learningenglish" in a["href"]), e.link)
    transcript = ""
    r = _get(page_url)
    if r:
        transcript = _text(r.text)
    return {
        "title": e.title,
        "url": page_url,
        "notes": notes.get_text(" ", strip=True)[:500],
        "transcript_excerpt": transcript[:4000],
    }


def lukes_english():
    feed = feedparser.parse(LUKES_RSS)
    if not feed.entries:
        _log("Luke's: no entries")
        return None
    e = feed.entries[0]
    return {"title": e.title, "url": e.link, "notes_excerpt": _text(getattr(e, "summary", ""))[:2000]}


# --- Chinese -----------------------------------------------------------------

HSK_RAW = ("https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary"
           "/main/wordlists/exclusive/new/{level}.json")
_hsk_cache: dict[int, list] = {}


def hsk_level_words(level: int):
    if level in _hsk_cache:
        return _hsk_cache[level]
    r = _get(HSK_RAW.format(level=level))
    words = []
    if r:
        for item in r.json():
            forms = item.get("forms") or [{}]
            tr = forms[0].get("transcriptions") or {}
            words.append({
                "simplified": item.get("simplified", ""),
                "pinyin": tr.get("pinyin", ""),
                "meanings": (forms[0].get("meanings") or [])[:3],
            })
    _hsk_cache[level] = words
    return words


# --- Tatoeba (shared) --------------------------------------------------------

def tatoeba_samples(lang: str, contains=None, n: int = 5):
    """Sample real example sentences from a local Tatoeba subset.

    Reads data/tatoeba_<lang>.tsv (lang = 'eng' or 'cmn'); each line ends with the
    sentence text. Returns [] if the file is absent (see prepare_tatoeba.py / README).
    """
    path = os.path.join(os.path.dirname(__file__), "data", f"tatoeba_{lang}.tsv")
    if not os.path.exists(path):
        return []
    try:
        matches = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                text = line.rstrip("\n").split("\t")[-1].strip()
                if not text:
                    continue
                if contains and not any(w and w in text for w in contains):
                    continue
                matches.append(text)
        random.shuffle(matches)
        return matches[:n]
    except OSError as e:
        _log(f"Tatoeba read failed: {e}")
        return []
