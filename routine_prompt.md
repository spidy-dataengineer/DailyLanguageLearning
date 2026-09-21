# Daily Language-Learning Routine — Prompt

You are running as a scheduled daily routine inside this repository. Your job: add
**30 English** (10 everyday · 10 business · 10 IELTS) and **10 beginner Chinese** expressions to two Notion databases,
sourced from real content, with **no repeats or near-duplicates**. The Python script
does all I/O; **you** do the language selection + expansion. Work in the repo directory.

## Steps

0. **Run `python daily_notion.py review` first** and report its output — it reschedules due cards
   (forgetting curve) and posts the active-recall review ping. Then continue with new items below.

1. Run these and read each one's JSON stdout:
   - `python daily_notion.py fetch en`
   - `python daily_notion.py fetch zh`

   Each prints: `today`, `target_count` (en 30, zh 10), `avoid` (every expression already saved —
   never repeat or near-repeat these), `candidates` (raw source material), and for zh
   `current_hsk_level`.

2. Build two JSON arrays of item objects — for English and Chinese — selecting from the
   candidates and expanding each into a full learning card.

   **English (30 items — 10 per purpose, a fixed split):**
   - **Split the 30 exactly: 10 `everyday` · 10 `business` · 10 `ielts`.** This is not a rotation —
     every run uses this split. `academic` / `travel` / `slang` / `idiom` remain valid tags for an
     item that naturally belongs there, but they get no reserved slots; use them inside the ten
     `everyday` slots when they fit.
   - **10 × `everyday`** — what people actually say in casual conversation: reactions, small talk,
     discourse markers, and idioms that are genuinely current. Anchors: "fair enough", "my bad",
     "read the room", "is this seat taken", "call it a day".
   - **10 × `business`** — workplace English usable today in a meeting, an email, or a stand-up.
     Anchors: "circle back", "loop someone in", "touch base", "align on", "I don't have the
     bandwidth for that", "let's take this offline".
   - **10 × `ielts`** — academic/exam vocabulary that raises a Writing or Speaking band: precise verbs
     and nouns, linking devices, and the **collocations** they live in. Give the collocation rather
     than the bare word whenever the word is normally used in one. Anchors: "a substantial proportion
     of", "mitigate the impact of", "consequently", "albeit", "pose a significant challenge".
     For these, `usage_note` must say where it earns marks (e.g. "IELTS Writing Task 2 — 원인·결과 연결").
   - **Frequency test — applies to the 20 `everyday` + `business` items:** if you cannot picture a real
     person saying it this month, at work or with friends, drop it and pick another. **No rare,
     literary, or archaic vocabulary, and no dictionary-headword curiosities.** The `ielts` slots are
     the only place formal, lower-frequency wording belongs — and even there it must be exam-useful,
     not obscure.
   - **The frequency test beats the count.** If you cannot find 10 genuinely common, not-yet-saved
     items for a slot, write fewer for that slot rather than filling it with rare wording, and say
     how many you wrote per slot in your final summary.
   - Material priority: (1) `candidates.inbox` (user-picked Instagram/YouTube — always use these
     first), (2) `candidates.bbc_phrases` (each episode title IS a real idiom/phrase) and
     `candidates.youtube` (latest uploads from everyday-English channels — the `title`/`description`
     usually name the target phrase; mine those), plus one of `candidates.bbc` / `lukes` (pick a
     *different* primary source than recent days, for variety). Use `candidates.tatoeba` for
     authentic example sentences. Candidates are seeds — prefer real, common usage over source rarity.
   - The `business` and `ielts` slots usually have **no seed** in `candidates`. Draw those from your
     own knowledge of current workplace usage and IELTS band-7+ vocabulary, set `source` to `Claude`,
     and leave `source_url` null. Only claim a real source when you actually used its material.

   **Chinese (10 items, beginner — 기초부터):**
   - Use `candidates.hsk` words (already filtered to unused, frequency order) as the backbone;
     use `candidates.tatoeba` for real example sentences; use `candidates.inbox` first if present.
   - Each `candidates.hsk` word lists its `readings` — one `{pinyin, meanings}` per pronunciation,
     with dictionary noise (surnames, `variant of` / `see` cross-references, archaic senses) already
     dropped. **When a word has 2+ readings, make ONE card that teaches every reading a learner at
     this level actually meets**, and skip readings that are rare, literary, or regional even if
     listed. E.g. 角 → jiǎo (모서리) + jué (角色 역할); 了 → le + liǎo; 的 → just `de`.
     - `pronunciation`: readings joined by ` / ` — `jiǎo · 지아오 / jué · 쥐에`
     - `meaning_ko`: numbered per reading — `① 모서리, 각 ② (角色) 역할`
     - `example` uses reading ①; `example2` + `example2_ko` use reading ② (required for these cards);
       a third reading goes in `usage_note`.
     A word with one reading stays a normal single-reading card.
   - `meanings` are in **dictionary order, not frequency order** — teach the sense a learner at
     this HSK level needs, which may not be listed first (后 → 뒤, 후 — not 황후; 干 gàn → 하다).
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
  "example2": "She joined mid-project but hit the ground running and caught up within days.",
  "example2_ko": "그녀는 프로젝트 중간에 합류했지만 곧바로 적응해 며칠 만에 따라잡았다.",
  "pronunciation": "/hɪt ðə ɡraʊnd ˈrʌnɪŋ/",
  "style": "idiom",
  "level": "EN-advanced",
  "usage_note": "새 일·역할을 빠르게 잘 시작한다는 뜻. 'start strong'보다 관용적.",
  "source": "BBC",
  "source_url": "https://www.bbc.co.uk/learningenglish",
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
- Provide a **second example** (`example2` + `example2_ko`) using the expression in a *different
  situation or genre* (e.g. one everyday, one work/academic/travel). It's shown as context inside the
  "뜻 보기" toggle (not blanked), so it needn't be cloze-safe but should still use the expression naturally.
  Chinese items may omit `example2` — except multi-reading cards, where it carries reading ②.
- Output strict JSON for the two files (no trailing commas, UTF-8, `ensure_ascii` off).
