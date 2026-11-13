"""Seed-content fetchers for the daily language-learning routine.

Each fetcher returns plain data (dict / list / None). Network calls fail soft:
on any error they log to stderr and return an empty result, so one dead source
never breaks the daily run. No Notion access here (that lives in daily_notion.py).
"""
from __future__ import annotations

import gzip
import os
import random
import re
import sys
from itertools import chain, zip_longest

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

BBC_6MIN_RSS = "https://podcasts.files.bbci.co.uk/p02pc9tn.rss"
BBC_TEWS_RSS = "https://podcasts.files.bbci.co.uk/p02pc9zn.rss"
LUKES_RSS = "https://teacherluke.co.uk/feed/"


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


def bbc_the_english_we_speak():
    """BBC 'The English We Speak'. Each episode title IS the target idiom/phrase (e.g. 'A hunch');
    same transcript-page pattern as the 6-minute feed."""
    feed = feedparser.parse(BBC_TEWS_RSS)
    if not feed.entries:
        _log("BBC TEWS: no entries")
        return None
    e = feed.entries[0]
    phrase = e.title.split(":", 1)[-1].strip() if ":" in e.title else e.title
    notes = BeautifulSoup(getattr(e, "summary", ""), "html.parser")
    page_url = next((a["href"] for a in notes.find_all("a", href=True)
                     if "learningenglish" in a["href"]), e.link)
    transcript = ""
    r = _get(page_url)
    if r:
        transcript = _text(r.text)
    return {"title": phrase, "url": page_url,
            "notes": notes.get_text(" ", strip=True)[:500], "transcript_excerpt": transcript[:4000]}


def lukes_english():
    feed = feedparser.parse(LUKES_RSS)
    if not feed.entries:
        _log("Luke's: no entries")
        return None
    e = feed.entries[0]
    return {"title": e.title, "url": e.link, "notes_excerpt": _text(getattr(e, "summary", ""))[:2000]}


# Everyday-English YouTube channels (name -> channel_id). Each new upload's title + description
# is seed material (learning-channel titles often contain the target phrase). Add/remove freely.
YT_CHANNELS = {
    "English with Lucy": "UCF6eEVtJokEFdaTDL5BKT4w",
    "Rachel's English": "UCvn_XCl_mgQmt3sD753zdJA",
    "Speak English With Vanessa": "UCxJGMJbjokfnr2-s4_RXPxQ",
    "Papa Teach Me": "UCwk6ifONlkvqnoMF2uyA05g",
    "BBC Learning English": "UCHaHD477h-FeBbVh9Sh7syA",
    "linguamarina": "UCDt4AwxX8H3BHiTNtmDu83Q",
}
YT_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={}"


def youtube_channels(per_channel: int = 1):
    """Latest upload(s) from each channel in YT_CHANNELS. Returns
    [{channel, title, description, url}]. Fail-soft per channel (the shim returns no
    entries on error, so one dead feed just contributes nothing)."""
    out = []
    for name, cid in YT_CHANNELS.items():
        for e in feedparser.parse(YT_FEED.format(cid)).entries[:per_channel]:
            out.append({"channel": name, "title": e.title,
                        "description": (getattr(e, "summary", "") or "")[:500], "url": e.link})
    return out


# --- Chinese -----------------------------------------------------------------

# "newest" = the HSK syllabus of November 2025 (level 1 is 300 words); "new" was the 2021 list.
HSK_RAW = ("https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary"
           "/main/wordlists/exclusive/newest/{level}.json")
_hsk_cache: dict[int, list] = {}

# Dictionary noise for a learner card: surnames, cross-references, archaic/regional-only senses.
_JUNK_SENSE = re.compile(
    r"^(surname|see |used in|abbr\. for|taiwan pr\.|\((archaic|classical|literary|tw)\)|(\w+ )?variant of)",
    re.I)


def _is_junk(form: dict) -> bool:
    pinyin = (form.get("transcriptions") or {}).get("pinyin", "")
    first = (form.get("meanings") or [""])[0] or ""
    return pinyin[:1].isupper() or bool(_JUNK_SENSE.match(first))  # capital pinyin = proper noun


def _readings(forms: list) -> list:
    """One {pinyin, meanings} per distinct pronunciation, junk senses dropped — unless that would
    leave nothing: 北京 / 中国 / 好玩儿 have only a proper-noun or erhua entry, and that entry IS the word."""
    kept = [f for f in forms if not _is_junk(f)] or forms
    by_pinyin: dict[str, list] = {}
    for f in kept:
        by_pinyin.setdefault((f.get("transcriptions") or {}).get("pinyin", ""), []).append(f.get("meanings") or [])
    readings = []
    for pinyin, lists in by_pinyin.items():
        # Interleave (1st sense of each entry, then 2nd, ...): dictionary order is etymological, so a
        # later entry's core sense (后 "back", after 后 "empress") must not be cut off by the cap.
        ms = []
        for m in chain.from_iterable(zip_longest(*lists)):
            if m and m not in ms:
                ms.append(m)
        readings.append({"pinyin": pinyin, "meanings": ms[:6]})
    return readings


def hsk_level_words(level: int):
    if level in _hsk_cache:
        return _hsk_cache[level]
    r = _get(HSK_RAW.format(level=level))
    words = []
    if r:
        for item in r.json():
            words.append({
                "simplified": item.get("simplified", ""),
                "readings": _readings(item.get("forms") or []),
            })
    _hsk_cache[level] = words
    return words


# --- Tatoeba (shared) --------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")  # built by prepare_sources.py
TATOEBA_URL = "https://tatoeba.org/en/sentences/show/{}"
_tatoeba_cache: dict[str, list] = {}


def _tatoeba(lang: str) -> list:
    """[{text, url}, ...] from data/tatoeba_<lang>.tsv (lang = 'eng' or 'cmn'); the url credits the sentence's author."""
    if lang not in _tatoeba_cache:
        rows = []
        try:
            with open(os.path.join(DATA_DIR, f"tatoeba_{lang}.tsv"), encoding="utf-8") as f:
                for line in f:
                    sid, _, text = line.rstrip("\n").partition("\t")
                    if text:
                        rows.append({"text": text, "url": TATOEBA_URL.format(sid)})
        except OSError as e:
            _log(f"Tatoeba read failed: {e}")
        _tatoeba_cache[lang] = rows
    return _tatoeba_cache[lang]


def tatoeba_samples(lang: str, contains=None, n: int = 5):
    """Random real sentences, optionally only those containing one of the given strings (Chinese words)."""
    rows = _tatoeba(lang)
    if contains:
        rows = [r for r in rows if any(w and w in r["text"] for w in contains)]
    return random.sample(rows, min(n, len(rows)))


def tatoeba_with_word(forms, n: int = 5):
    """Random English sentences using one of these word forms as a whole word (art must not match start)."""
    wanted = set(forms)
    rows = [r for r in _tatoeba("eng") if wanted & set(re.findall(r"[a-z']+", r["text"].lower()))]
    return random.sample(rows, min(n, len(rows)))


# --- English word lists (TSL: TOEIC, NAWL: academic) -----------------------------

def english_wordlist(name: str) -> list:
    """[{word, forms}, ...] for list 'TSL' or 'NAWL' from data/wordlist_en.tsv."""
    words = []
    try:
        with open(os.path.join(DATA_DIR, "wordlist_en.tsv"), encoding="utf-8") as f:
            for line in f:
                list_name, word, forms = line.rstrip("\n").split("\t")
                if list_name == name:
                    words.append({"word": word, "forms": forms.split(",")})
    except OSError as e:
        _log(f"Word list read failed: {e}")
    return words


# --- CC-CEDICT ---------------------------------------------------------------

_cedict_cache: dict[str, list] = {}
_CEDICT_LINE = re.compile(r"\S+ (\S+) \[([^\]]+)\] /(.+)/")


def cedict_readings(word: str) -> list:
    """[{pinyin, meanings}, ...] for a simplified word; [] when the dictionary doesn't have it (phrases often)."""
    if not _cedict_cache:
        try:
            with gzip.open(os.path.join(DATA_DIR, "cedict.txt.gz"), "rt", encoding="utf-8") as f:
                for line in f:
                    m = _CEDICT_LINE.match(line)
                    if m:
                        _cedict_cache.setdefault(m.group(1), []).append(
                            {"pinyin": m.group(2), "meanings": m.group(3).split("/")[:6]})
        except OSError as e:
            _log(f"CC-CEDICT read failed: {e}")
    return _cedict_cache.get(word, [])
