# content/ — sourcing & dedup (principles)

`sources.py` (fetch real seed material) + `dedup.py` (keep the corpus duplicate-free).

- Sources gather **raw material only** — no judgment, no generation. Each card records `Source` + `Source URL`.
- `import feedparser` resolves to the **root `feedparser.py` shim** (repo root is on `sys.path[0]`); keep it at root.
- Dedup is a **conservative safety net** (exact / case-punct variant / containment / reorder / ≥threshold).
  Morphological & semantic near-duplicates are the routine-Claude's job via the `avoid` list, not here.
- HSK progression walks levels low→high using already-saved words.
- Each HSK word → `readings` (`_readings`): junk dictionary entries dropped **unless** that leaves
  nothing (北京, 好玩儿), same-pinyin entries merged. Picking which readings to teach stays the routine's call.

Detail → [../docs/sources.md](../docs/sources.md) · [../docs/dedup.md](../docs/dedup.md)
