# Review (SRS — spaced repetition)

Code: `srs/review.py` (`due_rows`, `pick`, `reschedule`, `review`). Schema migration in `notion/notion_io.py` (`migrate`).

Each saved **vocab** card is reviewed on a forgetting curve. Practice rows (📝) are excluded.

## Scheme (Leitner, fixed intervals)
- Boxes 1→5, intervals **1 / 3 / 7 / 16 / 35 days** (`INTERVALS` in `constants.py`).
- New cards start **box 1**, `Next review = today + 1` (set in `notion_io._properties`).
- Feedback = the Notion **`Recall`** select (the ONLY field you touch): `Got it` → box +1 (max 5);
  `Forgot` → reset to box 1. Unrated due cards keep their box and are simply re-scheduled.
- **Daily cap** (`REVIEW_CAP` = 25 per language, `constants.py`): each run reviews every card with a
  `Recall` mark (a mark must never wait in the queue) plus the longest-waiting unmarked cards —
  oldest `Next review`, then oldest `Date` — up to the cap. The rest are left untouched, stay due,
  and come first the next day, so the deck rotates through at 25/language/day.
  Why (2026-09): almost nobody marks `Recall`, so every card sat in box 1 and the whole deck
  (2,364 cards) came due every day. The old single-message ping hid that by truncating at ~20
  cards; once pings were split across messages, the review tried to post all 2,364 and Discord
  rate-limited it (429) partway.
- Due = `Next review` empty **or** `<= today`. "today" = **Korea time** (`constants.kst_today`), so the
  08:00 KST cloud run (23:00 UTC) stamps and compares against the correct local day, not the UTC day.

## Daily flow — `python daily_notion.py review` (run first each day)
1. `due_rows()` finds due vocab cards in both DBs (skips practice rows = no `Meaning (KO)`).
   `pick()` takes today's slice (marked cards + up to the cap); only those go on.
2. `reschedule()` sets new `Box`, `Next review = today + INTERVALS[box]`, `Last reviewed = today`, clears `Recall`.
3. `notify_review()` posts a Discord ping: `• **expr** — ||meaning||` (meaning hidden = active recall); the header
   says how many due cards were held back. Skips if nothing due.

Usage: open the ping on your phone → recall the meaning → tap the spoiler to check → mark
`Got it`/`Forgot` in Notion when convenient. The next run reschedules accordingly.

## Properties (added by `migrate`)
`Box`(number) · `Next review`(date) · `Recall`(select: Got it/Forgot) · `Last reviewed`(date).
- One-time on existing DBs: `python daily_notion.py migrate` (idempotent; `data_sources.update`).
- Fresh `init` already includes them (`notion_io._SRS_PROPS` spread into `_EXPR_SCHEMA_BASE`).

## Notes
- Empty `Box`/`Next review` (pre-SRS rows) count as box 1 / due, so the first `review` lazily backfills them.
- Discord webhooks are one-way → feedback flows through Notion `Recall`, never Discord.
- Intervals are fixed Leitner (no SM-2 ease factors) — change `INTERVALS` in `constants.py` to retune.
- The review ping also embeds a stats footer (`stats.compute_stats` → `notify._stats_lines`).
- Browsing by period ≠ SRS: cards also carry `Year`/`Month`/`Week` selects (see [notion](notion.md)) so you can group a Notion view by Month→Week to re-read a given week's ~70 cards. That grouping is view-only; the forgetting-curve schedule above is independent of it.
