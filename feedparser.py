"""Minimal RSS/Atom feedparser shim for Python 3.11 (replaces broken feedparser 6.0.12)."""
import html
import re
import xml.etree.ElementTree as ET
import requests

_UA = "daily-lang-notion/1.0"

_XML_ENTS = (b"&amp;", b"&lt;", b"&gt;", b"&quot;", b"&apos;")


def _resolve_entities(content: bytes) -> bytes:
    """ElementTree only knows the 5 XML entities + numeric refs; WordPress/RSS feeds emit HTML
    named entities (&nbsp; &mdash; &hellip; …) that make ET.fromstring raise 'undefined entity'.
    Convert those to their UTF-8 bytes, leaving XML entities and numeric refs untouched."""
    def repl(m):
        ent = m.group(0)
        if ent in _XML_ENTS or ent.startswith(b"&#"):
            return ent
        return html.unescape(ent.decode("ascii", "ignore")).encode("utf-8")
    return re.sub(rb"&#?[0-9A-Za-z]+;", repl, content)
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

class _Entry:
    def __init__(self):
        self.title = ""
        self.link = ""
        self.summary = ""

class _Feed:
    def __init__(self):
        self.entries = []

def _text(el):
    return (el.text or "").strip() if el is not None else ""

def parse(url):
    feed = _Feed()
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": _UA})
        r.raise_for_status()
        root = ET.fromstring(_resolve_entities(r.content))
        tag = root.tag.lower()
        if "rss" in tag or root.tag == "rss":
            items = root.findall(".//item")
        else:
            items = (root.findall(".//{http://www.w3.org/2005/Atom}entry")
                     or root.findall(".//entry"))
        for item in items[:10]:
            e = _Entry()
            # NOTE: `find(a) or find(b)` is wrong here — an Element with no children is falsy,
            # so a text-only <title>/<description> would be skipped. Check `is not None`.
            t = item.find("title")
            if t is None:
                t = item.find("{http://www.w3.org/2005/Atom}title")
            e.title = _text(t)
            lk = item.find("link")
            if lk is not None:
                e.link = lk.text or lk.get("href", "")
            else:
                lk = item.find("{http://www.w3.org/2005/Atom}link")
                if lk is not None:
                    e.link = lk.get("href", "") or _text(lk)
            desc = None
            for tag_name in ("description", "summary",
                             "{http://www.w3.org/2005/Atom}summary",
                             "{http://purl.org/rss/1.0/modules/content/}encoded",
                             ".//{http://search.yahoo.com/mrss/}description"):  # YouTube media:description
                desc = item.find(tag_name)
                if desc is not None:
                    break
            e.summary = _text(desc)
            feed.entries.append(e)
    except Exception as ex:
        pass
    return feed
