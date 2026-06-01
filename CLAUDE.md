# CLAUDE.md — Daily Bilingual Expression Logger

Personal automation: pull real EN/ZH native expressions daily → **flashcards in two separate
Notion DBs** → **Discord** ping. Design docs (living source of truth): **start at `docs/overview.md`**.

## Layout (code ⇄ doc)
| Area | Code | Doc |
|---|---|---|
| CLI entry / dispatch | `daily_notion.py` | — |
| Notion API + schema + init/migrate + page layout + audio + fetch + write | `notion_io.py` | `docs/notion.md` |
| Source fetchers (MW, BBC, Luke's, HSK, Tatoeba) | `sources.py` | `docs/sources.md` |
| Dedup (skip same/similar) | `dedup.py` (`norm`, `similar`, `similar_to_any`, `hsk_candidates`) | `docs/dedup.md` |
| Review / SRS | `review.py` (`due_rows`, `reschedule`, `review`) | `docs/review.md` |
| Stats (read-only aggregates) | `stats.py` (`compute_stats`, `_streak`, `stats`) | `docs/stats.md` |
| Discord notifications | `notify.py` (`notify_write`, `notify_review`, `notify_stats`) | `docs/notify.md` |
| Shared constants | `constants.py` (STYLES, TARGETS, SIM_THRESHOLD, INTERVALS, …) | — |
| Content policy (level/count/style/pronunciation) | `routine_prompt.md`, `TARGETS` | `docs/generation.md` |
| Scheduling / deployment | — | `docs/deployment.md` |

Docs are split by **concern**, and code modules now mirror that split 1:1 — each concern has its
own `.py` and its own `docs/*.md`. `daily_notion.py` is a thin CLI entry that dispatches to the
concern modules, preserving the `python daily_notion.py <cmd>` surface used by `routine_prompt.md`.
If a module later grows into a folder, co-locate a short `README.md` per folder and keep this file
as the index.

## Working rules (this repo)
- **When you change behavior, update the matching `docs/` file in the same change** — keep code ⇄ docs in sync.
- **Python does I/O only** (`fetch` + `write`); all language generation happens inside the
  `/schedule` routine's own Claude — **no LLM API key**.
- **English and Chinese never mix** in one entry (two separate DBs + an Inbox DB).
- Secrets + DB IDs live in `.env` (gitignored) — never commit; never print the token/webhook value.
- Notion uses the **2025-09-03 data-source model** (notion-client 3.1.0): `data_sources.query`,
  `pages.create(parent=data_source_id)`; resolve via `data_source_id(db_id)`.
- CLI: `python daily_notion.py init <en_page> <zh_page> [inbox_page] | migrate | review | stats | fetch <en|zh> | write <en.json> <zh.json>`.

## Status / next
Built & live-verified (3 DBs, Discord notify, flashcards, Chinese practice). All four enhancements
in `docs/plan.md` shipped & live-verified: **SRS review · ZH pronunciation audio · cloze + reverse
cards · stats**. Next: move to a **personal PC → private GitHub repo → `/schedule`** (deferred; not
from the work machine, per company-policy concern). See `docs/deployment.md`.
