# srs/ — spaced repetition & stats (principles)

`review.py` (Leitner SRS) + `stats.py` (read-only aggregates).

- Leitner boxes 1–5, intervals **1/3/7/16/35 days** (`INTERVALS`). `Recall` (Got it/Forgot) is the only
  field the user marks; the next `review` run reschedules accordingly.
- "today" = **KST** (`kst_today`); due = `Next review` empty or ≤ today.
- Stats are **read-only** — derived from existing rows, no dashboard DB, no extra writes.
- Both import Notion helpers from `notion.notion_io`; neither generates or mutates card content.

Detail → [../docs/review.md](../docs/review.md) · [../docs/stats.md](../docs/stats.md)
