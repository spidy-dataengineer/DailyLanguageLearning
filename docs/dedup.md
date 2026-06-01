# Dedup — "skip already-saved or similar"

Code: `dedup.py` (`norm`, `similar`, `similar_to_any`, `hsk_candidates`). The write-time safety net is invoked from `notion_io.write`.

3 layers. **No vector DB needed at current scale.**

1. **String net (Python `similar()`)** — normalize (lowercase, strip punctuation), then match:
   exact / whole-phrase containment / token overlap / `difflib` ratio ≥ `SIM_THRESHOLD` (0.85).
   Deliberately conservative (avoids false positives like *affect* / *effect*). Catches exact + spelling variants.
2. **Semantic (routine Claude)** — the full `avoid` list (all saved expressions) is passed to the
   routine; Claude skips anything the same **or** semantically/morphologically similar
   (*take off* / *taking off*, synonyms, reworded idioms). This is the real meaning-level engine —
   more accurate than embedding cosine for idioms/nuance.
3. **Write-time net (Python)** — re-check each item vs existing rows before creating; skip collisions.

## Chinese
Dedup is just **set membership** over the finite HSK list (track used words → exclude from seeds).
No similarity computation needed; scales forever. The HSK "pointer" = walk levels low→high, take
the next unused words in frequency order.

## When a vector DB would help (not now)
Only once the **English history reaches thousands** (≈1 year at 10/day) and passing the whole
`avoid` list to Claude becomes heavy. Then:

> embed each candidate → cosine **top-K nearest** existing expressions → pass only those K to
> Claude for the final judgment. (Vector DB = pre-filter; Claude = decision.)

Simpler interim (no vector DB): pass only **recent N** (e.g. 500) + same category to `avoid`.
**Decision: add when needed, not before.**

Tuning: `SIM_THRESHOLD` in `constants.py` (lower = stricter / more skips).
