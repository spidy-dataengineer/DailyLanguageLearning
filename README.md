# Daily English + Chinese expressions → Notion

A daily automation that pulls real native expressions (podcasts, dictionary,
example sentences, plus your own Instagram/YouTube picks), writes **10 advanced English**
and **10 beginner Chinese** cards into two separate Notion databases, and pings you on
**Discord**. Built to run unattended as a Claude Code cloud routine (`/schedule`) — your PC
can be off.

- **English**: TOEIC 900+ / IELTS 8.0+ level, styles mixed (everyday / business / advanced-nuance).
- **Chinese**: from the basics, progressing through HSK in order.
- **No repeats**: 3-layer dedup (see below) skips anything already saved or too similar.
- **Flashcard layout**: each entry's Notion page shows the example first with the meaning hidden
  in a 👀 뜻 보기 toggle (active recall). Switch each DB to a **Gallery view** in Notion for
  card-style browsing.
- **Pronunciation**: English = IPA; Chinese = pinyin + 한글 (e.g. `ài hào · 아이 하오`).
- **Chinese practice**: each day also adds a 📝 연습 entry weaving the day's Chinese words into
  a few simple sentences (Korean hidden in toggles for active recall).

## How it works

```
fetch (Python)        → gathers real source material + the "avoid" list  → JSON
generate (routine AI) → picks & expands into 10 EN + 10 ZH cards         → en_items.json / zh_items.json
write (Python)        → creates Notion rows, marks inbox done, Discord ping
```

Python only does I/O. The routine's own Claude reasoning turns raw material into cards
(no separate LLM API key needed). See `routine_prompt.md` for the exact prompt.

## Files
- `daily_notion.py` — `init` / `fetch` / `write` (Notion + Discord I/O, dedup).
- `sources.py` — source fetchers: Merriam-Webster WOTD, BBC 6 Minute English (+transcript),
  Luke's English Podcast, HSK list, Tatoeba.
- `routine_prompt.md` — the `/schedule` prompt.
- `requirements.txt`, `.env.example`.
- `docs/` — design & planning docs (living source of truth); start at [docs/overview.md](docs/overview.md).

## One-time setup

1. **Notion connection** — https://www.notion.com/my-integrations → New connection (type:
   Internal) → copy the **Internal Integration Secret** into `NOTION_TOKEN`. Create two pages
   in Notion (one for English, one for Chinese); open each, `•••` → **Connections** → add your
   connection to **both**.

2. **Create the databases** — copy `.env.example` to `.env`, fill `NOTION_TOKEN`, then:
   ```
   python daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]
   ```
   (page ids = the 32-char id from each page URL; the Inbox DB defaults under the English
   page if `inbox_page_id` is omitted.) Paste the three printed `NOTION_DB_ID_*` lines into `.env`.

3. **Discord webhook** — Discord channel → Edit Channel → Integrations → Webhooks →
   New Webhook → Copy URL → `DISCORD_WEBHOOK_URL`.

4. *(optional)* **Tatoeba** — download per-language sentence files from
   https://tatoeba.org/en/downloads and save a subset as `data/tatoeba_eng.tsv` and
   `data/tatoeba_cmn.tsv` (tab-separated, sentence text in the last column). Absent = skipped.

## Local test (before scheduling)
```
python daily_notion.py fetch en          # inspect the raw material JSON
python daily_notion.py fetch zh
# hand-write a tiny en_items.json / zh_items.json, then:
python daily_notion.py write en_items.json zh_items.json   # rows appear in Notion + Discord ping
```

## Schedule it (cloud, PC off)
Push this repo to a private GitHub repo, then in Claude Code run `/schedule`: point it at the
repo, set the env vars from your `.env`, paste `routine_prompt.md` as the prompt, and pick a
daily time (min interval 1h). Use a one-off run to verify end-to-end.

> No Claude subscription / don't want a routine? The same script runs from **GitHub Actions
> cron** (add an `ANTHROPIC_API_KEY` and call the API to generate items) or **Windows Task
> Scheduler** (PC must be on).

## Manual drop: Instagram / YouTube
Automated scraping of Instagram/YouTube isn't reliable for unattended runs (IG has no public
API; YouTube transcripts are blocked from cloud IPs). Instead: when you find a reel/video you
like, add a row to the **Language Inbox** database — paste the URL into `Link`, set `Language`,
optionally paste the caption/transcript into `Raw text`. The next run processes unprocessed rows
first, extracts an expression, files it under the right language DB (Source = Instagram/YouTube),
and ticks `Processed`.

## Dedup (the "skip if similar" logic)
1. **Python pre-filter** (`fetch`) — normalizes existing expressions and drops near-identical
   seed candidates; over-provides candidates so the AI can pick alternatives.
2. **AI semantic skip** (`generate`) — given the full `avoid` list and told to skip morphological
   variants (take off / taking off) and semantic near-duplicates.
3. **Python safety net** (`write`) — re-checks each item against existing rows (exact / case /
   punctuation / containment / reordering / high string-similarity) and skips collisions.

## Tuning
- Daily volume: `TARGETS` in `daily_notion.py` (default `{"en": 10, "zh": 10}`).
- Similarity strictness: `SIM_THRESHOLD` (default 0.85; lower = stricter/more skips).
- English sources: constants near the top of `daily_notion.py` and `sources.py`.
