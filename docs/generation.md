# Generation (content policy)

The scheduled routine's Claude produces the daily items from `fetch` output, following
`routine_prompt.md`. This doc is the **policy/rationale**; edit both together when changing rules.

## Volume
`TARGETS = {"en": 10, "zh": 10}` in `daily_notion.py` → 20/day total. Ambitious — pair with review;
lower anytime. `fetch` over-provides candidates (e.g. ~20 HSK words) so dedup still leaves enough.
New cards enter the SRS review loop at box 1 — see [review](review.md).

## Level
- **English**: practical, **high-frequency everyday expressions** usable in real conversation —
  ~8 of 10 high-frequency, ~2 may be lower-frequency / more advanced. (The `Level` select stays the
  fixed label `EN-advanced` — it isn't aggregated in stats for EN, so re-labelling only churns Notion options.)
- **Chinese**: from **HSK1, in order** (progression tracked via the DB). Beginner-appropriate, short.

## Style (genre)
Six genres — `everyday` / `business` / `academic` / `travel` / `slang` / `idiom` (in `STYLES`,
`constants.py`) — spread across the English items **weighted toward the everyday end**, rotated for
coverage over the week (not all genres daily):
- `everyday` — casual reactions / small talk; `business` — workplace/email/meeting; `academic` —
  university/class/study (lectures, seminars, papers); `travel` — airport/hotel/directions; `slang` —
  current, genuinely-used colloquial slang (with a register `usage_note`); `idiom` — common idioms.
- **Practicality first**: prefer common, currently-used expressions; avoid rare/literary/archaic words.
  `candidates.merriam_webster` (Word-of-the-Day) is a **last-resort anchor only** — it skews obscure.
  (Retired the old `situational` tag — its café/travel/shopping content now lives under `travel`/`everyday`.)

Chinese stays everyday-focused while at beginner level (no genre tag needed).

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
BBC **The English We Speak** (`candidates.bbc_phrases`) is an idiom/phrase seed — each episode title
is itself a real phrase (e.g. "read the room"); its cards record `Source` = `BBC` (shared label).

## Chinese practice
Append one `{"type":"practice","sentences":[{zh,pinyin,ko}…]}` (3–4 sentences weaving the day's
words). English has none yet — could add for parity later.

## Item contract (JSON)
`expression` · `meaning_ko` · `example` · `example_ko` · `example2` · `example2_ko` · `pronunciation` ·
`style` · `level` · `usage_note` · `source` · `source_url` · `inbox_page_id`. Exact schema + example in `routine_prompt.md`.
- **`example` must contain `expression` verbatim** — the card blanks it out (`____`) for cloze active recall
  (`cloze()`), and a reverse `거꾸로` toggle drills meaning→expression. If the expression isn't found, the blank
  is skipped (fail-soft) and the full sentence is shown.
- **`example2` / `example2_ko`** (English; ZH may omit): a second real usage in a *different situation/genre*,
  rendered as context inside the `뜻 보기` toggle (not blanked). Stored in `Example 2` / `Example 2 (KO)`.
