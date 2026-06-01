# CLAUDE.md — Daily Bilingual Expression Logger

Personal automation: pull real EN/ZH native expressions daily → **flashcards in two separate
Notion DBs** → **Discord** ping. Design docs (living source of truth): **start at `docs/overview.md`**.

## Layout (code ⇄ doc)
| Area | Code | Doc |
|---|---|---|
| Source fetchers | `sources.py` | `docs/sources.md` |
| Notion I/O + schema + card/practice layout | `daily_notion.py` | `docs/notion.md` |
| Dedup (skip same/similar) | `daily_notion.py` (`similar`, `hsk_candidates`) | `docs/dedup.md` |
| Review / SRS | `daily_notion.py` (`review`, `due_rows`, `reschedule`) | `docs/review.md` |
| Content policy (level/count/style/pronunciation) | `routine_prompt.md`, `TARGETS` | `docs/generation.md` |
| Scheduling / deployment | — | `docs/deployment.md` |

Docs are split by **concern, not by file**: `daily_notion.py` holds several concerns, so its
sub-topics each get a doc; `sources.py` maps 1:1 to `docs/sources.md`. (If the code later grows
into many files/folders, co-locate a short `README.md` per folder and keep this file as the index.)

## Working rules (this repo)
- **When you change behavior, update the matching `docs/` file in the same change** — keep code ⇄ docs in sync.
- **Python does I/O only** (`fetch` + `write`); all language generation happens inside the
  `/schedule` routine's own Claude — **no LLM API key**.
- **English and Chinese never mix** in one entry (two separate DBs + an Inbox DB).
- Secrets + DB IDs live in `.env` (gitignored) — never commit; never print the token/webhook value.
- Notion uses the **2025-09-03 data-source model** (notion-client 3.1.0): `data_sources.query`,
  `pages.create(parent=data_source_id)`; resolve via `data_source_id(db_id)`.
- CLI: `python daily_notion.py init <en_page> <zh_page> [inbox_page] | migrate | review | fetch <en|zh> | write <en.json> <zh.json>`.

## Status / next
Built & live-verified (3 DBs, Discord notify, flashcards, Chinese practice). Next: move to a
**personal PC → private GitHub repo → `/schedule`** (deferred; not from the work machine, per
company-policy concern). See `docs/deployment.md`.
