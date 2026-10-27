# Dedup — "skip already-saved or similar"

Code: `content/dedup.py` (`norm`, `similar`, `similar_to_any`, `check_candidates`, `hsk_candidates`). The write-time safety net is invoked from `notion/notion_io.py` (`write`); the routine's pre-check is `daily_notion.py check`.

3 layers. **No vector DB needed at current scale.**

1. **String net (Python `similar()`)** — normalize (lowercase, strip punctuation), then match:
   exact / whole-phrase containment / token overlap / `difflib` ratio ≥ `SIM_THRESHOLD` (0.85).
   Deliberately conservative (avoids false positives like *affect* / *effect*). Catches exact + spelling variants.
2. **Semantic (routine Claude, via `check`)** — the routine picks ~1.5× its target, then runs
   `daily_notion.py check <en|zh> <file>`. `check_candidates` sorts each pick into `duplicates`
   (fails the string net → drop), `check_meaning` (shares a content word — English stems such as
   take/taking → `tak`, or 2+ Chinese characters — with saved expressions, listed in `related`, max 8)
   and `clear`. Claude judges only the `related` lists for morphological/semantic repeats.
   2026-10-27 change: before this, `fetch` printed the full saved list as `avoid` (5,807 English
   rows ≈ 118KB of the 130KB fetch output, growing 30 rows a day). Now `fetch` prints `saved_count`
   only (English fetch ≈ 12KB). `check` on 45 picks takes ~20s and prints ~4KB.
   Known gap: irregular forms (*take* / *took*) share no stem — Claude still has to notice those.
3. **Write-time net (Python)** — re-check each item vs existing rows before creating; skip collisions.

## Chinese
Dedup is just **set membership** over the finite HSK list (track used words → exclude from seeds).
No similarity computation needed; scales forever. The HSK "pointer" = walk levels low→high, take
the next unused words in frequency order.

## When a vector DB would help (not now)
`check` already does the "pre-filter, then Claude decides" split with word overlap instead of
embeddings. Embeddings would only add synonyms that share no word (*postpone* / *put off*).
**Decision: add when needed, not before.**

Tuning: `SIM_THRESHOLD` in `constants.py` (lower = stricter / more skips).
