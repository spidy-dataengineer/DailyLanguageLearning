# Stats (read-only aggregates)

Code: `stats.py` (`_streak`, `compute_stats`, `stats`). Discord lines are formatted by `notify._stats_lines` and dispatched by `notify.notify_stats`.

Learning progress derived **entirely from existing rows** — no dashboard DB, no new properties, no state fields.

## Metrics (`compute_stats`)
One pass over the EN + ZH databases (vocab rows only — rows with both `Expression` and `Meaning (KO)`;
the daily practice row is skipped). Per language:
- **total** — vocab cards saved
- **due** — cards with `Next review` empty or `<= today` (same rule as [`due_rows`](review.md))
- **boxes** — Leitner box distribution (`Box` number)
- **hsk** (ZH only) — `Level` select distribution (`HSK1`–`HSK6`)

Plus, across both:
- **streak** — consecutive days (with ≥1 card `Date`) counting back from today, or from yesterday if
  nothing is dated today yet (so it reads correctly before the day's `write` runs)
- **total** — EN + ZH combined

All values are computed live from the Notion rows; nothing is stored.

## Delivery
- **`stats` CLI mode** — `python daily_notion.py stats` prints the full JSON to stdout **and** posts a
  Discord summary (`notify.notify_stats`). On-demand; read-only (never writes to Notion).
- **Review-ping footer** — `review.review` appends a 3-line summary (`notify._stats_lines`: totals + streak,
  box distribution, ZH HSK distribution) to the active-recall ping. The "due" count is not repeated in the
  footer — the ping header already shows how many are due, and the footer is computed *after* rescheduling.

## Notes
- Read-only: needs no schema change and never mutates rows; safe to run anytime.
- `due` here matches `due_rows` exactly (verified by cross-check), so it stays consistent with the SRS loop.
