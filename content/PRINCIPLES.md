# content/ — sourcing & dedup (principles)

`sources.py` (fetch real seed material) + `dedup.py` (keep the corpus duplicate-free).

- Sources gather **raw material only** — no judgment, no generation. Each card records `Source` + `Source URL`.
- `import feedparser` resolves to the **root `feedparser.py` shim** (repo root is on `sys.path[0]`); keep it at root.
- Dedup is a **conservative safety net** (exact / case-punct variant / containment / reorder / ≥threshold).
  Morphological & semantic near-duplicates are the routine-Claude's job via the `avoid` list, not here.
- HSK progression walks levels low→high using already-saved words.

Detail → [../docs/sources.md](../docs/sources.md) · [../docs/dedup.md](../docs/dedup.md)
