"""Checks a card against the script-checkable rules of docs/card-quality.md before it is written.

A refused card is left out of the write so the routine fixes it and writes it again.
The wrong options have their own check (`options_check.py`).
"""
from __future__ import annotations

import re

# 설명-01: editing notes and field labels kept from the old Notion pages, which learners see after answering.
_NOTES = re.compile(r"원래 (표기|예문)|(^|[\s/])EN\s*:|(노트|종류)\s*[:：]")
_DASH = re.compile(r"[—–―]")
# 예문-02: only examples far too short or too long, the same for every level (2026-11-17 user decision: "너무 길거나
# 너무 짧지만 않으면", about three sentences at most). Words in English, characters in Chinese.
_SHORTEST, _LONGEST = 3, 30


def example_size(example: str, lang: str) -> int:
    if lang == "zh":
        return len(re.sub(r"[\s\W_]", "", example))
    return len(example.split())


def check_card(item: dict, lang: str) -> str | None:
    """Why the card is refused, or None."""
    name = (item.get("expression") or "").strip()
    note = item.get("usage_note") or ""
    if _NOTES.search(note):
        return f"{name}: 설명에 메모·틀 이름 ({_NOTES.search(note).group(0).strip()})"
    if not note.strip():
        return f"{name}: 설명이 비어 있음"
    example = item.get("example") or ""
    if _DASH.search(example):
        return f"{name}: 예문에 줄표"
    size = example_size(example, lang)
    if not _SHORTEST <= size <= _LONGEST:
        unit = "자" if lang == "zh" else "단어"
        return f"{name}: 예문이 {size}{unit} ({_SHORTEST}~{_LONGEST}{unit} 밖)"
    return None
