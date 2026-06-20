# PRINCIPLES.md — repo root (project map)

Top-level index of the codebase. Detail lives in [docs/overview.md](docs/overview.md); per-module
invariants live in each folder's `PRINCIPLES.md` (linked below).

## Root files — and why they stay at root
- `daily_notion.py` — the CLI entry (`python daily_notion.py <cmd>`). Running it from the repo root puts
  the root on `sys.path[0]`, which is what lets the concern packages import with **no install**. Pinned.
- `constants.py` — shared leaf (`STYLES`, `TARGETS`, `SIM_THRESHOLD`, `INTERVALS`, `kst_today`,
  `period_labels`); imported by every module, zero project deps.
- `feedparser.py` — local shim shadowing the pip package; resolves as a top-level `import feedparser`
  **only** because root is on the path. Pinned (a move falls through to the pip package).
- `CLAUDE.md` (project instructions + index, auto-loaded by Claude Code) · `README.md` ·
  `requirements.txt` / `requirements-dev.txt` · `routine_prompt.md` (the `/schedule` generation prompt) ·
  `MIGRATION.md`.

## Concern packages — each carries its own `PRINCIPLES.md`
- [notion/](notion/PRINCIPLES.md) — Notion gateway: API client, schema, init/migrate, page layout, audio, fetch, write.
- [content/](content/PRINCIPLES.md) — sourcing (`sources.py`) + dedup/HSK progression (`dedup.py`).
- [srs/](srs/PRINCIPLES.md) — spaced-repetition review (`review.py`) + read-only stats (`stats.py`).
- [notify/](notify/PRINCIPLES.md) — Discord webhook senders (`notify.py`).
- `tests/` — pytest suite (run `pytest` from the repo root). · `docs/` — detailed per-concern docs + cross-cutting (overview, deployment, plan, generation).

## Data flow
`review` (resurface due cards) → `fetch en|zh` (gather raw material) → the routine's Claude generates the
day's cards → `write` (create Notion rows + Discord ping) → `stats` (read-only aggregates). **Python does
I/O only**; all language generation happens inside the `/schedule` routine's Claude — no LLM API key.

## Whole-project invariants
- English & Chinese never mix — two separate DBs + an Inbox DB.
- Secrets / DB IDs live in `.env` (gitignored) — never commit or print the token/webhook.
- Notion uses the **2025-09-03 data-source model** (`data_sources.query`, `pages.create(parent=data_source_id)`).
- Code ⇄ docs stay in sync in the same change; follow the **Workflow discipline** loop in `CLAUDE.md`.
