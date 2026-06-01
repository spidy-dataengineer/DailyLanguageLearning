# Overview — Daily Bilingual Expression Logger

Personal automation: every day, pull real native **English & Chinese** expressions from real
sources, write them as **flashcards** into two separate Notion databases, and notify on **Discord**.

## Pipeline
```
fetch (Python, I/O) → generate (routine Claude) → write (Python, I/O) → Discord notify
```
- **review** — (run first each day) resurface due cards on the forgetting curve + an active-recall Discord ping. See [review](review.md).
- **fetch** — gather real source material + the `avoid` list (already-saved expressions). No judgment.
- **generate** — the scheduled routine's own Claude turns raw material into 10 EN + 10 ZH cards
  (+ 1 Chinese practice entry), honoring level/style/dedup rules. See [generation](generation.md).
- **write** — create Notion rows + flashcard page bodies, mark inbox processed, Discord ping.

Python never calls an LLM API — generation happens inside the Claude routine, so **no API key**.

## Components
| File | Role | Doc |
|---|---|---|
| `sources.py` | seed fetchers (MW, BBC, Luke's, HSK, Tatoeba) | [sources](sources.md) |
| `daily_notion.py` | Notion+Discord I/O, dedup, card/practice layout, init/fetch/write | [notion](notion.md), [dedup](dedup.md) |
| `routine_prompt.md` | the generation prompt given to `/schedule` | [generation](generation.md) |
| `.env` | secrets + DB IDs (gitignored) | — |

## Key decisions (log)
- Runtime: Claude Code **cloud routine** (`/schedule`) — PC can be off, uses Max (no API key). See [deployment](deployment.md).
- Notion writes via **REST API** (`notion-client`), not MCP — static token = unattended-safe, deterministic, precise dedup queries.
- Notification: **Discord webhook** (static URL → phone push).
- **English & Chinese kept fully separate** — two DBs/pages, never merged in one entry.
- Instagram/YouTube: **manual-drop Inbox**, not scraping (no API / ToS / cloud-IP blocks).
- Volume **10 + 10/day**; pronunciation EN=IPA, ZH=pinyin+한글; **flashcard (active-recall)** layout.

## Status & roadmap
- ✅ Code built & live-verified; 3 Notion DBs; Discord notify; flashcard + Chinese practice + **SRS review** live.
- ⏳ **Move to personal PC → private GitHub repo → `/schedule`** (deferred; not from the work machine).
- v2 backlog: pronunciation audio, embedding pre-filter for dedup at scale, English practice sentences, richer Discord embed.

> The original plan-mode plan is at `~/.claude/plans/elegant-snacking-dragon.md` (history). These `docs/` are the living source of truth.
