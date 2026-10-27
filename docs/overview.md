# Overview — Daily Bilingual Expression Logger

Personal automation: every day, pull real native **English & Chinese** expressions from real
sources, write them as **flashcards** into two separate Notion databases, and notify on **Discord**.

## Pipeline
```
fetch (Python, I/O) → generate (routine Claude) → write (Python, I/O) → Discord notify
```
- **review** — manual only since 2026-10-27 (the Language Quiz app's sync schedules reviews now): resurface due cards on the forgetting curve + an active-recall Discord ping (with a stats footer). See [review](review.md).
- **stats** — (on-demand) read-only learning aggregates → JSON + Discord summary. See [stats](stats.md).
- **fetch** — gather real source material + `saved_count`. No judgment. zh also lists `sns`: posts the sns-classifier saved to "중국어 저장게시물" in the last 7 days that no card cites yet (since 2026-10-27; they become extra cards on top of the 10).
- **check** — sort the routine's picks into already-saved / shares-a-word / clear (`content/dedup.py`).
- **generate** — the scheduled routine's own Claude turns raw material into 30 EN + 10 ZH cards
  (+ 1 Chinese practice entry), honoring level/style/dedup rules. See [generation](generation.md).
- **write** — create Notion rows + flashcard page bodies, mark inbox processed, Discord ping.

Python never calls an LLM API — generation happens inside the Claude routine, so **no API key**.

## Components
| File | Role | Doc |
|---|---|---|
| `daily_notion.py` | CLI entry point — thin dispatcher to the modules below | — |
| `notion_io.py` | Notion API + schema/init + page layout + audio + fetch + write | [notion](notion.md) |
| `dedup.py` | similarity-based dedup + HSK progression | [dedup](dedup.md) |
| `review.py` | SRS review (Leitner intervals) | [review](review.md) |
| `stats.py` | read-only learning aggregates | [stats](stats.md) |
| `notify.py` | Discord webhook senders | [notify](notify.md) |
| `sources.py` | seed fetchers (MW, BBC 6-min + The English We Speak, YouTube channels, Luke's, HSK, Tatoeba) | [sources](sources.md) |
| `constants.py` | shared constants (STYLES, TARGETS, SIM_THRESHOLD, INTERVALS, …) | — |
| `routine_prompt.md` | the generation prompt given to `/schedule` | [generation](generation.md) |
| `.env` | secrets + DB IDs (gitignored) | — |

## Key decisions (log)
- Runtime: Claude Code **cloud routine** (`/schedule`) — PC can be off, uses Max (no API key). See [deployment](deployment.md).
- Notion writes via **REST API** (`notion-client`), not MCP — static token = unattended-safe, deterministic, precise dedup queries.
- Notification: **Discord webhook** (static URL → phone push).
- **English & Chinese kept fully separate** — two DBs/pages, never merged in one entry.
- Instagram/YouTube: **manual-drop Inbox**, not scraping (no API / ToS / cloud-IP blocks).
- Volume **30 EN (10 everyday · 10 business · 10 IELTS) + 10 ZH/day**; pronunciation EN=IPA, ZH=pinyin+한글; **flashcard (active-recall)** layout.

## Status & roadmap
- ✅ Code built & live-verified; 3 Notion DBs; Discord notify; flashcard + Chinese practice + **SRS review** + **ZH pronunciation audio** (inline native recording: audio-cmn → Wikimedia Commons, YouGlish-link fallback) live.
- ⏳ **Move to personal PC → private GitHub repo → `/schedule`** (deferred; not from the work machine).
- Enhancement plan (`docs/plan.md`): ✅ SRS · ✅ audio (ZH) · ✅ cloze + reverse cards · ✅ stats — **all four shipped**.
- v2 backlog: EN audio (one-line gate), embedding pre-filter for dedup at scale, English practice sentences, richer Discord embed.

> The original plan-mode plan is at `~/.claude/plans/elegant-snacking-dragon.md` (history). These `docs/` are the living source of truth.
