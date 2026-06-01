# Notify — Discord webhook output

Code: `notify.py`. Three senders + one shared formatter, all using a single `DISCORD_WEBHOOK_URL` env var.

## Pings

| Function | Caller | When it fires |
|---|---|---|
| `notify_write(written)` | `notion_io.write` | After daily `write` succeeds — lists today's new EN/ZH cards with meanings visible. Footer: links to each DB. |
| `notify_review(due, stats)` | `review.review` | Daily SRS review — lists due cards with meanings hidden as `\|\|spoilers\|\|`. Footer: `_stats_lines`. |
| `notify_stats(s)` | `stats.stats` | On-demand stats CLI — pure aggregate summary. |

All three:
- No-op if `DISCORD_WEBHOOK_URL` is unset (logs and returns).
- No-op if nothing to send (`notify_write` skips when both lists are empty; `notify_review` skips when `due` is empty).
- Truncate `content` at 1990 chars (Discord's 2000-char limit, with margin).
- Fail-soft: `RequestException` is caught and logged; the routine continues.

## Shared formatter — `_stats_lines(s)`

Builds the 1–3 lines used by both `notify_review` (as footer) and `notify_stats` (as body):
```
📊 누적 240개 (🇬🇧 120 · 🇨🇳 120) · 🔥 연속 12일
📦 박스 1:58 2:49 3:40 4:50 5:43
🇨🇳 HSK HSK1:50 HSK2:70
```

The HSK line is omitted when the ZH stats have no `hsk` field.

## Why one module
All three pings share Discord's content-length cap, `requests.post` boilerplate, and the stats formatter — keeping them together avoids triple-copying that surface. The flip side: any module that pings now imports `notify`, so `notify` itself depends on nothing app-internal (only `os`, `requests`, `datetime`).
