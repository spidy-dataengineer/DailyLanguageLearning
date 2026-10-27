"""Similarity / dedup primitives — Python safety net for catching duplicate expressions.

Catches exact repeats, case/punctuation variants, whole-phrase containment, reordering,
and >=threshold string similarity. Does NOT try to catch morphological inflections
(take off / taking off) or semantic synonyms — that's the routine-Claude's job.
"""
from __future__ import annotations

import difflib
import re
import sys

from content import sources
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
    (e.g. affect/effect). Those are the routine-Claude's job: check_candidates() hands it the
    saved expressions that share a word with each pick to judge."""
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


_CJK = re.compile(r"[一-鿿]")
_STOP = {"the", "and", "for", "you", "your", "its", "it's", "are", "was", "with", "that", "this",
         "not", "but", "out", "off", "about", "into", "from", "what", "have", "has", "get", "got",
         "one", "all", "can", "just", "like", "who", "how", "why", "when", "there", "they"}
RELATED_LIMIT = 8


def _stem(word: str) -> str:
    for suffix in ("ing", "ied", "ies", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def _keys(s: str) -> set:
    """Chinese: its characters. English: stems of its content words (take/taking/takes -> tak)."""
    n = norm(s)
    if _CJK.search(n):
        return set(_CJK.findall(n))
    return {_stem(w) for w in n.split() if len(w) >= 3 and w not in _STOP}


def check_candidates(candidates, existing) -> dict:
    """Sort the routine's candidate expressions against what is already saved.

    duplicates    — the write step would skip these (same test as write()), so replace them
    check_meaning — share a word/character with saved expressions; the routine's Claude decides
                    whether one is the same expression in another form or a near-synonym
    clear         — nothing close was found
    Replaces handing Claude the whole saved list (5,800+ English rows, ~118KB) every morning.
    """
    keyed = [(e, _keys(e)) for e in existing]
    out = {"duplicates": [], "check_meaning": [], "clear": []}
    accepted = []
    for cand in candidates:
        matches = [e for e in existing if similar(cand, e)] or [a for a in accepted if similar(cand, a)]
        if matches:
            out["duplicates"].append({"candidate": cand, "matches": matches[:RELATED_LIMIT]})
            continue
        accepted.append(cand)
        ck, nc = _keys(cand), norm(cand)
        need = 2 if _CJK.search(nc) else 1  # one shared character (好, 的) means nothing
        scored = []
        for e, ek in keyed:
            shared = len(ck & ek)
            if shared >= need or (_CJK.search(nc) and nc in norm(e)):
                scored.append((-shared, e))
        if scored:
            related = [e for _, e in sorted(scored)[:RELATED_LIMIT]]
            out["check_meaning"].append({"candidate": cand, "related": related})
        else:
            out["clear"].append(cand)
    return out


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
