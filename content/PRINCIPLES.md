# content/ — sourcing & dedup (principles)

`sources.py` (fetch real seed material) + `dedup.py` (keep the corpus duplicate-free).

- Sources gather **raw material only** — no judgment, no generation. Each card records `Source` + `Source URL`.
- `import feedparser` resolves to the **root `feedparser.py` shim** (repo root is on `sys.path[0]`); keep it at root.
- Dedup is a **conservative safety net** (exact / case-punct variant / containment / reorder / ≥threshold).
  Morphological & semantic near-duplicates are the routine-Claude's job via `daily_notion.py check`, not here.
- HSK progression walks levels low→high using already-saved words.
- Each HSK word → `readings` (`_readings`): junk dictionary entries dropped **unless** that leaves
  nothing (北京, 好玩儿), same-pinyin entries merged. Picking which readings to teach stays the routine's call.

- `card_check.py` + `options_check.py` test a card and its wrong options against `docs/card-quality.md` before
  `notion_io.write` / `add_options` / `lint` let them into the database. Only rules a script can test live here;
  the judgment rules are the routine-Claude's. `options_check` counts option reuse from `db.cards_db.option_uses`.

Detail → [../docs/sources.md](../docs/sources.md) · [../docs/dedup.md](../docs/dedup.md) · [../docs/card-quality.md](../docs/card-quality.md)
