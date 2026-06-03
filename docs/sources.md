# Sources (`sources.py`)

Each fetcher returns plain data and **fails soft** (logs to stderr, returns empty) so one dead
source never breaks the run.

## English
| Source | Feed/URL | Auth | Cloud reliability | Status |
|---|---|---|---|---|
| Merriam-Webster WOTD | `merriam-webster.com/wotd/feed/rss2` | none | high (RSS) | ✅ |
| BBC 6 Minute English | `podcasts.files.bbci.co.uk/p02pc9tn.rss` (+ transcript page) | none | high | ✅ |
| BBC The English We Speak | `podcasts.files.bbci.co.uk/p02pc9zn.rss` (+ transcript page) | none | high | ✅ episode title = target phrase |
| YouTube channels | `youtube.com/feeds/videos.xml?channel_id=…` per channel (`sources.YT_CHANNELS`) | none | high | ✅ latest uploads' title + description; allowlist `youtube.com` |
| Luke's English Podcast | `teacherluke.co.uk/feed/` | none | high | ✅ |
| Tatoeba | `data/tatoeba_eng.tsv` subset | none | high (local file) | optional (no file) |

## Chinese
| Source | Where | Auth | Status |
|---|---|---|---|
| HSK list | `drkameleon/complete-hsk-vocabulary` raw JSON, per level | none | ✅ progression backbone |
| Tatoeba | `data/tatoeba_cmn.tsv` subset | none | optional |

## Not sources (handled by manual-drop Inbox)
- **YouTube transcripts** — blocked from cloud/datacenter IPs (2026); only video descriptions are reliably fetchable.
- **Instagram** — no usable public API; third-party scrapers are paid/brittle/ToS-violating.

## Adding a source
1. Write a `*_fetch()` in `sources.py` returning a dict/list; wrap the network call in `_get` or a `try/except` so it fails soft.
2. Add it to the `candidates` dict in `notion_io.fetch()` (en or zh branch).
3. Mention it in `routine_prompt.md` so the routine knows to mine it.
