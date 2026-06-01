"""Similarity / dedup primitives — Python safety net for catching duplicate expressions.

Catches exact repeats, case/punctuation variants, whole-phrase containment, reordering,
and >=threshold string similarity. Does NOT try to catch morphological inflections
(take off / taking off) or semantic synonyms — that's the routine-Claude's job.
"""
from __future__ import annotations

import difflib
import re
import sys

import sources
from constants import MAX_HSK_LEVEL, SIM_THRESHOLD


def _log(msg: str) -> None:
    print(f"[daily] {msg}", file=sys.stderr)


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
    short, long = sorted([na, nb], key=len)
    if len(short) >= 4 and re.search(rf"\b{re.escape(short)}\b", long):
        return True
    ta, tb = set(na.split()), set(nb.split())
    if len(ta) > 1 and len(tb) > 1 and len(ta & tb) / len(ta | tb) >= 0.8:
        return True
    return difflib.SequenceMatcher(None, na, nb).ratio() >= threshold


def similar_to_any(cand: str, existing, threshold: float = SIM_THRESHOLD) -> bool:
    return any(similar(cand, e, threshold) for e in existing)


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
