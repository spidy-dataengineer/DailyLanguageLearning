# Sources (`sources.py`)

Each fetcher returns plain data and **fails soft** (logs to stderr, returns empty) so one dead
source never breaks the run.

## English
| Source | Feed/URL | Auth | Cloud reliability | Status |
|---|---|---|---|---|
| BBC 6 Minute English | `podcasts.files.bbci.co.uk/p02pc9tn.rss` (+ transcript page) | none | high | ✅ |
| BBC The English We Speak | `podcasts.files.bbci.co.uk/p02pc9zn.rss` (+ transcript page) | none | high | ✅ episode title = target phrase |
| YouTube channels | `youtube.com/feeds/videos.xml?channel_id=…` per channel (`sources.YT_CHANNELS`) | none | high | ✅ latest uploads' title + description; allowlist `youtube.com` |
| Luke's English Podcast | `teacherluke.co.uk/feed/` | none | high | ✅ |
| Tatoeba | `data/tatoeba_eng.tsv` subset | none | high (local file) | optional (no file) |

## Chinese
| Source | Where | Auth | Status |
|---|---|---|---|
| HSK list | `drkameleon/complete-hsk-vocabulary` raw JSON, per level | none | ✅ progression backbone; each word → `readings` (see below) |
| Tatoeba | `data/tatoeba_cmn.tsv` subset | none | optional |

## Dropped
- **Merriam-Webster Word-of-the-Day** (removed 2026-09) — the RSS feed worked fine, but its word is
  deliberately rare/literary and was the main reason English cards drifted obscure, even while the
  prompt flagged it "last resort". Removed the fetcher, the `MW_WOTD_RSS` constant, and the
  `candidates.merriam_webster` key. `Merriam-Webster` stays in `EN_SOURCES` so cards already written
  keep their label.

## HSK readings (`_readings`)
Each word in the source carries several dictionary entries (`forms`). Taking only `forms[0]` (the old
behavior) handed the routine 360 of the 5,363 HSK 1–6 words with a useless first entry — 角 as
"surname Jue", 克 as "abbr. for Croatia", 句 as "variant of 勾" — and dropped real second readings
(行 xíng). Now every word becomes `readings: [{pinyin, meanings}]`:
- Drop junk entries: capitalised pinyin (surname / place name) and senses starting `surname`,
  `see`, `used in`, `abbr. for`, `Taiwan pr.`, `(archaic|classical|literary|Tw)`, `… variant of`.
- **Unless that leaves nothing** — 59 words (北京, 中国, 汉语, 星期天, 春节, 好玩儿 …) have only a
  proper-noun or erhua entry, and that entry *is* the word, so it stays.
- Merge entries with the same pinyin (72 words, e.g. 后 hòu ×2) by **interleaving** their senses, 6 max:
  dictionary order is etymological, so 后 lists "empress" before "back" and 干 gàn lists "to do"
  fifth — a cap of 3 would cut both core HSK1 senses off.
- Result over HSK 1–6: 1 reading ≈ 5,000 words, 2 ≈ 250, 3+ ≈ 35. Which of a 3+ word's readings a
  beginner needs (的 → just `de`) is a language call, left to the routine — see
  [generation](generation.md#chinese-multi-reading-cards).

## Not sources (handled by manual-drop Inbox)
- **YouTube transcripts** — blocked from cloud/datacenter IPs (2026); only video descriptions are reliably fetchable.
- **Instagram** — no usable public API; third-party scrapers are paid/brittle/ToS-violating.

## Adding a source
1. Write a `*_fetch()` in `sources.py` returning a dict/list; wrap the network call in `_get` or a `try/except` so it fails soft.
2. Add it to the `candidates` dict in `notion_io.fetch()` (en or zh branch).
3. Mention it in `routine_prompt.md` so the routine knows to mine it.
