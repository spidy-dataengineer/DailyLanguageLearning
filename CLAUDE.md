# CLAUDE.md — Daily Bilingual Expression Logger

Personal automation: pull real EN/ZH native expressions daily → **flashcards in two separate
Notion DBs** → **Discord** ping. Design docs (living source of truth): **start at `docs/overview.md`**.

## Layout (code ⇄ doc)
| Area | Code | Doc |
|---|---|---|
| CLI entry / dispatch | `daily_notion.py` | — |
| Notion API + schema + init/migrate + page layout + audio + fetch + write | `notion/notion_io.py` | `docs/notion.md` · `notion/PRINCIPLES.md` |
| Source fetchers (MW, BBC 6-min + The English We Speak, YouTube channels, Luke's, HSK, Tatoeba) | `content/sources.py` | `docs/sources.md` · `content/PRINCIPLES.md` |
| Inbox ingestion (manual picks + auto-source roadmap) | `notion/notion_io.py` (`inbox_unprocessed`) | `docs/inbox.md` |
| Dedup (skip same/similar) | `content/dedup.py` (`norm`, `similar`, `similar_to_any`, `hsk_candidates`) | `docs/dedup.md` · `content/PRINCIPLES.md` |
| Review / SRS | `srs/review.py` (`due_rows`, `reschedule`, `review`) | `docs/review.md` · `srs/PRINCIPLES.md` |
| Stats (read-only aggregates) | `srs/stats.py` (`compute_stats`, `_streak`, `stats`) | `docs/stats.md` |
| Discord notifications | `notify/notify.py` (`notify_write`, `notify_review`, `notify_stats`) | `docs/notify.md` · `notify/PRINCIPLES.md` |
| Shared constants | `constants.py` (STYLES, TARGETS, SIM_THRESHOLD, INTERVALS, …) — repo root | — |
| Content policy (level/genre/count/pronunciation) | `routine_prompt.md`, `TARGETS` | `docs/generation.md` |
| Scheduling / deployment | — | `docs/deployment.md` |

Code is grouped into **concern folders** — `notion/` (Notion gateway), `content/` (sources + dedup),
`srs/` (review + stats), `notify/` (Discord) — each with a short `PRINCIPLES.md` describing the module's
role, its invariants, and how it connects to the others. **Read a module's `PRINCIPLES.md` before working
in that folder** (they aren't auto-loaded; the Layout table above indexes them, code ⇄ doc). `daily_notion.py`, `constants.py`, and the `feedparser.py` shim
stay at the **repo root**: `daily_notion.py` is the CLI entry (keeping the `python daily_notion.py <cmd>`
surface), and root-on-`sys.path[0]` lets the packages import with **no install** and keeps the bare
`import feedparser` resolving to the local shim. `docs/` remains the detailed source + cross-cutting
overview; this file stays the index.

## Working rules (this repo)
- **When you change behavior, update the matching `docs/` file in the same change** — keep code ⇄ docs in sync.
- **Python does I/O only** (`fetch` + `write`); all language generation happens inside the
  `/schedule` routine's own Claude — **no LLM API key**.
- **English and Chinese never mix** in one entry (two separate DBs + an Inbox DB).
- Secrets + DB IDs live in `.env` (gitignored) — never commit; never print the token/webhook value.
- Notion uses the **2025-09-03 data-source model** (notion-client 3.1.0): `data_sources.query`,
  `pages.create(parent=data_source_id)`; resolve via `data_source_id(db_id)`.
- CLI: `python daily_notion.py init <en_page> <zh_page> [inbox_page] | migrate | review | stats | fetch <en|zh> | write <en.json> <zh.json>`.

## Workflow discipline
On every change that adds, edits, or deletes files, follow this loop:
1. **Survey first** — skim the whole codebase before touching it; never edit a file in isolation.
2. **Keep it organized by concern folder** — each module lives in its folder (`notion/`, `content/`,
   `srs/`, `notify/`; the CLI entry + shared leaves stay at root). A new concern gets its own folder and
   the related files moved in — don't let the root drift back to flat.
3. **Per-folder `PRINCIPLES.md`** — every concern folder has one: each file's role, its invariants, and
   **how it connects to the other modules** (who imports it / what it calls). It isn't auto-loaded, so
   **read the relevant module's `PRINCIPLES.md` before working in that folder** (this root `CLAUDE.md`
   indexes them in the Layout table), and update it in the same change. Detailed prose lives in `docs/*.md`.
4. **Living checklist (two levels)** — maintain a running list of what's implemented vs. still to add,
   **per-module and whole-project**. Review it when starting work and keep it current as you go: tick what's
   done, add each gap you discover. Mirror longer-lived items into `docs/plan.md` so they survive the session.

## Status / next
Built & live-verified (3 DBs, Discord notify, flashcards, Chinese practice). All four enhancements
in `docs/plan.md` shipped & live-verified: **SRS review · ZH pronunciation audio · cloze + reverse
cards · stats**. Next: move to a **personal PC → private GitHub repo → `/schedule`** (deferred; not
from the work machine, per company-policy concern). See `docs/deployment.md`.
