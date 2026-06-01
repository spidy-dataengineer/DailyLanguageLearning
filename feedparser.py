"""Minimal RSS/Atom feedparser shim for Python 3.11 (replaces broken feedparser 6.0.12)."""
import xml.etree.ElementTree as ET
import requests

_UA = "daily-lang-notion/1.0"
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
        root = ET.fromstring(r.content)
        tag = root.tag.lower()
        if "rss" in tag or root.tag == "rss":
            items = root.findall(".//item")
        else:
            items = (root.findall(".//{http://www.w3.org/2005/Atom}entry")
                     or root.findall(".//entry"))
        for item in items[:10]:
            e = _Entry()
            t = (item.find("title") or item.find("{http://www.w3.org/2005/Atom}title"))
            e.title = _text(t)
            lk = item.find("link")
            if lk is not None:
                e.link = lk.text or lk.get("href", "")
            else:
                lk = item.find("{http://www.w3.org/2005/Atom}link")
                if lk is not None:
                    e.link = lk.get("href", "") or _text(lk)
            desc = (item.find("description")
                    or item.find("summary")
                    or item.find("{http://www.w3.org/2005/Atom}summary")
                    or item.find("{http://purl.org/rss/1.0/modules/content/}encoded"))
            e.summary = _text(desc)
            feed.entries.append(e)
    except Exception as ex:
        pass
    return feed
