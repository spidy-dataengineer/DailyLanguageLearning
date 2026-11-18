"""Checks a card's three written wrong options before they reach the quiz app (rules: docs/options.md).

The same tests as the app repo's former scripts/distractors/add.ts: an option the app would throw away, or one
that would give the answer away, is refused here so the card is offered again instead.
"""
from __future__ import annotations

import re

_NOT_WORD = re.compile(r"[\s\W_]+")
_ASIDE = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_CUTS_SHORT = re.compile(r"[,;①-⑩]| / ")
# 오답-01 (docs/card-quality.md): the longest wrong meaning is at least this share of the answer's, or the answer
# stands out by its length (the meaning answer was the longest of four in 49.8% of English cards). Expressions may
# differ a little more: a few letters show less than a few Korean syllables.
_NEAR_LENGTH = 0.8
_NEAR_EXPRESSION = 0.7
# The other way round: padding every wrong meaning to pass the check above leaves the answer the shortest of four
# (literally = 말 그대로 among 때때로 이따금씩, 보통 대개의 경우에; 2026-11-17 rewrite). One wrong meaning has to be
# about as short as the answer: at most this share longer, or 2 characters for short answers.
_NEAR_LENGTH_UP = 1.25
# 오답-08: how many cards one expression may be a wrong option for, before learners learn to skip it (老师 was on 79).
# Chinese is higher: level 1 has only 300 words to choose from.
MOST_USES = {"en": 5, "zh": 8}


def _plain(s: str) -> str:
    return _NOT_WORD.sub(" ", (s or "").lower()).strip()


def option_key(expression: str) -> str:
    """One wrong option however it is spelt or marked, for counting how often it is used."""
    return _plain(expression)


def _senses(s: str) -> set[str]:
    return {p for p in (_plain(x) for x in re.split(r"[,;/·]", _ASIDE.sub(" ", s or ""))) if p}


def check_options(card: dict, options, used: dict[str, int] | None = None, lang: str = "en") -> tuple[str | None, list[str]]:
    """(why the options are refused, or None) and warnings that still let them in.

    `card` needs expression, meaning_ko and example; `options` is [[expression, meaning], x3]. `used` counts, by
    `option_key`, the cards each expression is already a wrong option for.
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
    shown = re.split(r"[,;]| / ", _ASIDE.sub("", card.get("meaning_ko", "")))[0].strip()
    if max(len(m) for _, m in options) < _NEAR_LENGTH * len(shown):
        return f"{name}: 오답 뜻이 다 정답 ({shown}) 보다 많이 짧음, 가장 긴 보기가 정답이 됨", []
    if min(len(m) for _, m in options) > max(_NEAR_LENGTH_UP * len(shown), len(shown) + 2):
        return f"{name}: 오답 뜻이 다 정답 ({shown}) 보다 많이 김, 가장 짧은 보기가 정답이 됨. 꾸밈말을 붙여 늘리지 말고 길이가 비슷한 오답을 고름", []
    if max(len(e) for e, _ in options) < _NEAR_EXPRESSION * len(name):
        return f"{name}: 오답 표현이 다 정답보다 많이 짧음", []
    for e, _ in options:
        if (used or {}).get(option_key(e), 0) >= MOST_USES[lang]:
            return f"{name}: {e} 는 이미 {used[option_key(e)]}장의 오답", []

    warnings = []
    example = card.get("example", "")
    before = example.lower().split(name.lower())[0].rstrip() if name else ""
    for e, _ in options:
        if re.search(r"\ban$", before) and not re.match(r"[aeiou]", e, re.I):
            warnings.append(f"{name}: an 뒤에 {e}")
        if re.search(r"\ba$", before) and re.match(r"[aio]", e, re.I):
            warnings.append(f"{name}: a 뒤에 {e}")
    return None, warnings
