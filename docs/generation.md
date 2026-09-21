# Generation (content policy)

The scheduled routine's Claude produces the daily items from `fetch` output, following
`routine_prompt.md`. This doc is the **policy/rationale**; edit both together when changing rules.

## Volume
`TARGETS = {"en": 30, "zh": 10}` in `constants.py` → 40/day total. Ambitious — pair with review;
lower anytime. `fetch` over-provides candidates (e.g. ~20 HSK words) so dedup still leaves enough.
New cards enter the SRS review loop at box 1 — see [review](review.md).
**The frequency test beats the count**: at 10 per slot per day the pool of genuinely common
expressions thins out over months, so a slot may come in under 10 rather than be padded with rare
wording; the run reports the per-slot count.

## Level
- **English**: a **fixed split by purpose** — 10 everyday · 10 business · 10 IELTS (see Style below).
  The 20 everyday+business items must pass a frequency test; the 10 IELTS items are the only slots where
  formal, lower-frequency wording is allowed. (The `Level` select stays the fixed label `EN-advanced` —
  it isn't aggregated in stats for EN, so re-labelling only churns Notion options.)
- **Chinese**: from **HSK1, in order** (progression tracked via the DB). Beginner-appropriate, short.

## Style (genre)
Seven genres — `everyday` / `business` / `ielts` / `academic` / `travel` / `slang` / `idiom` (in
`STYLES`, `constants.py`). The English 30 use a **fixed split, every run**: **10 `everyday` · 10
`business` · 10 `ielts`**. The other four tags stay valid labels for an item that naturally belongs
there, but hold no reserved slots — they ride inside the ten `everyday` ones.
- `everyday` — casual reactions / small talk / current idioms; `business` — workplace, email, meeting;
  `ielts` — academic/exam vocabulary and the collocations it lives in, with `usage_note` naming where
  it earns marks; `academic` — university/class/study; `travel` — airport/hotel/directions; `slang` —
  current colloquial slang (with a register `usage_note`); `idiom` — common idioms.
- **Why fixed rather than rotated** (2026-09): the old "rotate genres, weighted toward everyday"
  wording let rare and literary words through. The 20 everyday+business items now carry a frequency
  test — *would a real person say this at work or with friends this month?* — and `ielts` is the only
  slot where formal, lower-frequency wording is allowed, and even there it must be exam-useful.
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
Real seed (podcast / HSK / Tatoeba / Inbox) → Claude expands. Each card
records `Source` + `Source URL`. **Inbox items (user-picked IG/YouTube) are used first.**
The `business` and `ielts` slots usually have **no seed** in `candidates` — Claude supplies them from
its own knowledge and records `Source` = `Claude`, `Source URL` = null. `Source` is written unvalidated
(`notion_io.py`); `EN_SOURCES` only seeds the select options at `init`, so old labels survive.
BBC **The English We Speak** (`candidates.bbc_phrases`) is an idiom/phrase seed — each episode title
is itself a real phrase (e.g. "read the room"); its cards record `Source` = `BBC` (shared label).

## Chinese multi-reading cards
A 多音字 like 角 (jiǎo 모서리 / jué 역할) becomes **one card covering every reading a learner at the
current HSK level meets** — not two cards (same expression → the second would be deduped away).
`pronunciation` joins readings with ` / `, `meaning_ko` numbers them (① ②), `example` shows
reading ①, `example2` reading ② (required here), a third goes in `usage_note`. Rare/literary/
regional readings are skipped even when listed (的 → just `de`). Audio: audio-cmn is keyed by the
character, so the card gets one recording (usually the common reading); the Commons fallback
matches on the joined pinyin.

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
