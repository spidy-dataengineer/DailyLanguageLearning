"""Discord webhook notifications — three flavors: daily write summary, review ping, stats."""
from __future__ import annotations

import os
import sys

import requests

from constants import kst_today


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


def _stats_lines(s: dict) -> list:
    en, zh = s["by_lang"]["en"], s["by_lang"]["zh"]
    boxes: dict = {}
    for e in (en, zh):
        for k, v in e["boxes"].items():
            boxes[k] = boxes.get(k, 0) + v
    lines = [f"📊 누적 {s['total']}개 (🇬🇧 {en['total']} · 🇨🇳 {zh['total']}) · 🔥 연속 {s['streak']}일",
             "📦 박스 " + (" ".join(f"{k}:{boxes[k]}" for k in sorted(boxes)) or "—")]
    if zh.get("hsk"):
        lines.append("🇨🇳 HSK " + " ".join(f"{k}:{v}" for k, v in zh["hsk"].items()))
    return lines


def notify_write(written: dict) -> None:
    """Discord ping for the daily-write summary: lists each new card grouped by language."""
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        _log("no DISCORD_WEBHOOK_URL; skipping notification")
        return
    if not (written.get("en") or written.get("zh")):
        _log("nothing written; skipping notification")
        return
    lines = [f"📚 **오늘의 표현** ({kst_today().isoformat()})"]
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


def notify_review(due: dict, stats: dict | None = None) -> None:
    """Discord ping for SRS review: due cards with meanings hidden as ||spoilers||."""
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    n = len(due["en"]) + len(due["zh"])
    if not url or n == 0:
        _log("review: nothing due or no webhook; skipping ping")
        return
    lines = [f"🧠 **복습 ({kst_today().isoformat()}) — {n}개** · 뜻은 ||가림||, 기억했으면 Notion에서 Recall 표시"]
    for lang, flag in (("en", "🇬🇧 English"), ("zh", "🇨🇳 中文")):
        if due[lang]:
            lines += ["", f"**{flag}**"]
            lines += [f"• **{r['expression']}** — ||{r['meaning_ko']}||" for r in due[lang]]
    if stats:
        lines += [""] + _stats_lines(stats)
    try:
        requests.post(url, json={"content": "\n".join(lines)[:1990]}, timeout=20).raise_for_status()
    except requests.RequestException as e:
        _log(f"review ping failed: {e}")


def notify_stats(s: dict) -> None:
    """Discord ping for the stats CLI command."""
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        _log("no DISCORD_WEBHOOK_URL; skipping stats notification")
        return
    lines = [f"📈 **학습 통계 ({s['today']})**"] + _stats_lines(s)
    try:
        requests.post(url, json={"content": "\n".join(lines)[:1990]}, timeout=20).raise_for_status()
    except requests.RequestException as e:
        _log(f"stats notify failed: {e}")
