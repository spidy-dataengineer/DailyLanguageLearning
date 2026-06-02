# Daily Language-Learning Routine — Prompt

You are running as a scheduled daily routine inside this repository. Your job: add
**10 everyday English** and **10 beginner Chinese** expressions to two Notion databases,
sourced from real content, with **no repeats or near-duplicates**. The Python script
does all I/O; **you** do the language selection + expansion. Work in the repo directory.

## Steps

0. **Run `python daily_notion.py review` first** and report its output — it reschedules due cards
   (forgetting curve) and posts the active-recall review ping. Then continue with new items below.

1. Run these and read each one's JSON stdout:
   - `python daily_notion.py fetch en`
   - `python daily_notion.py fetch zh`

   Each prints: `today`, `target_count` (10), `avoid` (every expression already saved —
   never repeat or near-repeat these), `candidates` (raw source material), and for zh
   `current_hsk_level`.

2. Build two JSON arrays of item objects — for English and Chinese — selecting from the
   candidates and expanding each into a full learning card.

   **English (10 items — practical everyday expressions):**
   - Aim for expressions a learner can actually USE in daily life and real conversation.
     Calibration anchors: "fair enough", "read the room", "can I make it to-go instead of drink it here".
   - **Ratio (important): ~8 of 10 must be high-frequency, everyday-usable expressions;
     ~2 may be lower-frequency or more advanced.** Do not fill the list with rare/literary vocabulary.
   - Spread the 10 across four styles, weighted toward the everyday end; vary day to day:
     - `everyday` — casual reactions / discourse / small talk ("no worries", "my bad", "fair enough").
     - `situational` — functional phrases for a scenario: café/ordering, travel, shopping, appointments
       ("can I get this to-go", "could we split the bill", "is this seat taken").
     - `idiom` — common idioms/colloquialisms people actually say ("read the room", "call it a day").
     - `business` — workplace / email / meeting phrasing ("circle back", "loop someone in", "touch base").
   - Material priority: (1) `candidates.inbox` (user-picked Instagram/YouTube — always use these
     first), (2) `candidates.bbc_phrases` (each episode title IS a real idiom/phrase) and one of
     `candidates.bbc` / `lukes` (pick a *different* primary source than recent days, for variety),
     (3) `candidates.merriam_webster` as an occasional anchor. Use `candidates.tatoeba` for
     authentic example sentences when helpful. Candidates are seeds — prefer real, common usage
     over whatever happens to be rare in the source.

   **Chinese (10 items, beginner — 기초부터):**
   - Use `candidates.hsk` words (already filtered to unused, frequency order) as the backbone;
     use `candidates.tatoeba` for real example sentences; use `candidates.inbox` first if present.
   - Keep it beginner-appropriate: short, high-frequency, simple sentences. `level` =
     `HSK<current_hsk_level>`.
   - **Also append ONE practice object at the END of the Chinese array** that weaves several of
     the day's Chinese words into 3–4 very simple sentences (beginner-level):
     `{"type": "practice", "sentences": [{"zh": "我爸爸的爱好是看书。", "pinyin": "wǒ bàba de àihào shì kàn shū", "ko": "우리 아빠의 취미는 독서야."}, ...]}`.
     Use as many of the day's words as fit naturally. (English array has no practice object.)

   **Both languages — DEDUP (critical):** Do NOT output any expression that is the same as, OR
   similar to, anything in `avoid`. "Similar" includes morphological variants
   (take off / taking off / took off) and semantic near-duplicates (synonyms, the same idiom
   reworded). If a candidate collides with `avoid`, **skip it and choose another** — extra
   candidates are provided for exactly this reason.

   **Inbox items:** extract the single most useful expression from the link / `raw_text`; set
   `source` to `Instagram` or `YouTube` (based on the link), `source_url` to the link, and
   `inbox_page_id` to that row's `inbox_page_id` so the script marks it processed.

3. Write the arrays to `en_items.json` and `zh_items.json` in the repo (UTF-8).

4. Run: `python daily_notion.py write en_items.json zh_items.json`
   It creates the rows, marks processed inbox items, and posts the Discord summary. Report its output.

## Item schema (each object in the arrays)

```json
{
  "expression": "to hit the ground running",
  "meaning_ko": "시작하자마자 곧바로 잘 해내다",
  "example": "The new manager hit the ground running, closing three deals in her first week.",
  "example_ko": "새 매니저는 부임하자마자 첫 주에 거래 세 건을 성사시키며 곧바로 성과를 냈다.",
  "pronunciation": "/hɪt ðə ɡraʊnd ˈrʌnɪŋ/",
  "style": "idiom",
  "level": "EN-advanced",
  "usage_note": "새 일·역할을 빠르게 잘 시작한다는 뜻. 'start strong'보다 관용적.",
  "source": "Merriam-Webster",
  "source_url": "https://www.merriam-webster.com/word-of-the-day",
  "inbox_page_id": null
}
```

Chinese items use the same fields, except **`pronunciation` = pinyin with tone marks PLUS a
Korean phonetic (한글)**, joined by ` · ` — e.g. `ài hào · 아이 하오`. `level` = `HSK1`,
`source` = `HSK` / `Tatoeba` / `Instagram` / `YouTube`. (English `pronunciation` stays IPA only.)

## Notes
- If a `fetch` returns few candidates (a source was down), still produce the full `target_count`
  from the available material plus your own knowledge of common usage, keeping the dedup rule.
- Keep examples natural and genuinely useful; the Korean gloss/translation should read naturally.
- The card shows the `example` with the expression **blanked out** (`____`) for active recall, hides
  `meaning_ko` + the full `example_ko` behind a "뜻 보기" toggle, and adds a reverse "거꾸로" toggle.
  So `example` **must contain the `expression` verbatim** (exact same wording, so the blank works) in
  real context, and the Korean lines must be accurate.
- Output strict JSON for the two files (no trailing commas, UTF-8, `ensure_ascii` off).
