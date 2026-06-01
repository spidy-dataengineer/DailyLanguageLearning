# Generation (content policy)

The scheduled routine's Claude produces the daily items from `fetch` output, following
`routine_prompt.md`. This doc is the **policy/rationale**; edit both together when changing rules.

## Volume
`TARGETS = {"en": 10, "zh": 10}` in `daily_notion.py` → 20/day total. Ambitious — pair with review;
lower anytime. `fetch` over-provides candidates (e.g. ~20 HSK words) so dedup still leaves enough.
New cards enter the SRS review loop at box 1 — see [review](review.md).

## Level
- **English**: TOEIC 900+ / IELTS 8.0+ — idioms, collocations, nuance, low-frequency vocab. Avoid basic words.
- **Chinese**: from **HSK1, in order** (progression tracked via the DB). Beginner-appropriate, short.

## Style
Three styles — `everyday` / `business` / `advanced-nuance` — **randomly mixed** across the English
items and varied day to day. Chinese stays everyday-focused while at beginner level.

## Pronunciation
- English = **IPA** only (e.g. `/ˈpælətəbl̩/`).
- Chinese = **pinyin + 한글** (e.g. `ài hào · 아이 하오`).
- **Audio (ZH)**: Python attaches a **native-speaker recording** as an inline Notion audio block via
  `native_audio_url`: first [audio-cmn](https://github.com/hugolpz/audio-cmn) (CC BY-SA, HEAD-checked CDN, ~80%
  of single HSK words), then **Wikimedia Commons** (pinyin-verified against the card's pinyin so the wrong word's
  audio is never attached). Falls back to a YouGlish search link (`youglish_url`) when neither has a recording —
  typically multi-char phrases/idioms. No new field for Claude, no upload/hosting, no API key. EN audio gated off (one-line flip).

## Sourcing (hybrid)
Real seed (podcast / dictionary / HSK / Tatoeba / Inbox) → Claude expands. Each card
records `Source` + `Source URL`. **Inbox items (user-picked IG/YouTube) are used first.**

## Chinese practice
Append one `{"type":"practice","sentences":[{zh,pinyin,ko}…]}` (3–4 sentences weaving the day's
words). English has none yet — could add for parity later.

## Item contract (JSON)
`expression` · `meaning_ko` · `example` · `example_ko` · `pronunciation` · `style` · `level` ·
`usage_note` · `source` · `source_url` · `inbox_page_id`. Exact schema + example in `routine_prompt.md`.
- **`example` must contain `expression` verbatim** — the card blanks it out (`____`) for cloze active recall
  (`cloze()`), and a reverse `거꾸로` toggle drills meaning→expression. If the expression isn't found, the blank
  is skipped (fail-soft) and the full sentence is shown. No new fields — pure rendering.
