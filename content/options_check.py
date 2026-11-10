"""Checks a card's three written wrong options before they reach the quiz app (rules: docs/options.md).

The same tests as the app repo's former scripts/distractors/add.ts: an option the app would throw away, or one
that would give the answer away, is refused here so the card is offered again instead.
"""
from __future__ import annotations

import re

_NOT_WORD = re.compile(r"[\s\W_]+")
_ASIDE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_CUTS_SHORT = re.compile(r"[,;①-⑩]| / ")


def _plain(s: str) -> str:
    return _NOT_WORD.sub(" ", (s or "").lower()).strip()


def _senses(s: str) -> set[str]:
    return {p for p in (_plain(x) for x in re.split(r"[,;/·]", _ASIDE.sub(" ", s or ""))) if p}


def check_options(card: dict, options) -> tuple[str | None, list[str]]:
    """(why the options are refused, or None) and warnings that still let them in.

    `card` needs expression, meaning_ko and example; `options` is [[expression, meaning], x3].
    """
    name = card.get("expression", "")
    if (not isinstance(options, list) or len(options) != 3
            or any(not isinstance(o, list) or len(o) != 2 or not str(o[0]).strip() or not str(o[1]).strip()
                   for o in options)):
        return f"{name}: 오답 3개가 아님", []
    answer = _plain(name)
    seen: set[str] = set()
    for e, _ in options:
        v = _plain(e)
        if not v or v in answer or answer in v or v in seen:
            return f"{name}: 정답과 겹치거나 중복 ({e})", []
        seen.add(v)
    meaning = _plain(card.get("meaning_ko", ""))
    own = _senses(card.get("meaning_ko", ""))
    for _, m in options:
        pm = _plain(m)
        if pm in meaning or meaning in pm or _senses(m) & own:
            return f"{name}: 뜻이 정답과 겹침 ({m})", []
    for _, m in options:
        if _CUTS_SHORT.search(m):
            return f"{name}: 뜻에 쉼표·세미콜론 ({m})", []

    warnings = []
    shown = re.split(r"[,;]| / ", _ASIDE.sub("", card.get("meaning_ko", "")))[0].strip()
    if len(shown) - max(len(m) for _, m in options) >= 8:
        warnings.append(f"{name}: 오답 뜻이 정답 ({shown}) 보다 8자 이상 짧음, 가장 긴 보기가 정답이 됨")
    example = card.get("example", "")
    before = example.lower().split(name.lower())[0].rstrip() if name else ""
    for e, _ in options:
        if re.search(r"\ban$", before) and not re.match(r"[aeiou]", e, re.I):
            warnings.append(f"{name}: an 뒤에 {e}")
        if re.search(r"\ba$", before) and re.match(r"[aio]", e, re.I):
            warnings.append(f"{name}: a 뒤에 {e}")
    return None, warnings
