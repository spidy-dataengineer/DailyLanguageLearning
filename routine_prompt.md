# Daily Language-Learning Routine — Prompt

You are running as a scheduled daily routine inside this repository. Your job: add
**30 English** (10 everyday · 10 business · 10 IELTS) and **30 beginner Chinese** expressions as cards,
sourced from real content, with **no repeats or near-duplicates**. The Python script
does all I/O; **you** do the language selection + expansion. Work in the repo directory.

The cards' source is the quiz app's database (Supabase). Each card is written there first, then to the
English / Chinese Notion database as a backup page. This environment adds the database key to those requests
on its own; you never see or need it, so do not look for it.

## Required environment variables (exact names)

`NOTION_TOKEN`, `NOTION_DB_ID_EN`, `NOTION_DB_ID_ZH`, `NOTION_DB_ID_INBOX`, `DISCORD_WEBHOOK_URL`.

Check them **only** with `python daily_notion.py check-env` (prints names + lengths, never values).
Do not look for any other variable name and do not guess names such as `NOTION_EN_DB_ID` — they do not
exist. Continue when it prints `"ok": true`; if it lists a name under `missing`, stop and report
exactly that name.

Then run `python daily_notion.py check-db`. It reads one card id from the database. Continue when it prints
`"ok": true`; otherwise stop and report the `status` it printed (401 means the database key isn't reaching it).

## Steps

0. **Do not run `python daily_notion.py review`.** Review scheduling (`Box`, `Recall`, `Next review`)
   now belongs to the Language Quiz app and its sync; running `review` here would count the app's
   answers a second time. Start at step 1.

1. Run these and read each one's JSON stdout:
   - `python daily_notion.py fetch en`
   - `python daily_notion.py fetch zh`

   Each prints: `today`, `target_count` (en 30, zh 30), `saved_count` (how many expressions are
   already saved — the list itself is not printed; step 3 checks your picks against it),
   `candidates` (raw source material, including `candidates.sns` saved posts for both languages), and for zh
   `current_hsk_level`.

2. Choose the day's expressions for English and Chinese from the candidates (rules below);
   steps 3–4 check them and expand each into a full learning card.

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
   - **`level` = how hard the meaning is for a Korean learner, `EN1`–`EN7`** (CEFR-based; the app's
     level test and difficulty filter read it). Judge each card on its own; the slot does not set it.
     - `EN1` A1–A2: basic words, greetings, short daily phrases — "How are you?", "I'm hungry"
     - `EN2` early B1: very common phrasal verbs and short replies — "pick up", "my bad", "fair enough"
     - `EN3` late B1: common outside textbooks, basic work words — "call it a day", "follow up"
     - `EN4` early B2: general work/news words, common idioms — "circle back", "cut corners", "consequently"
     - `EN5` late B2: less common idioms, formal words, widespread slang — "a can of worms", "albeit"
     - `EN6` C1: advanced words, subtle meanings, rarer idioms — "pedantic", "toe the line"
     - `EN7` C2: rare literary or technical words — "palimpsest", "recondite"
     Most `everyday`/`business` cards land in `EN1`–`EN4`, most `ielts` cards in `EN4`–`EN6`.
   - **The frequency test beats the count.** If you cannot find 10 genuinely common, not-yet-saved
     items for a slot, write fewer for that slot rather than filling it with rare wording, and say
     how many you wrote per slot in your final summary.
   - Material priority: (1) `candidates.inbox` (user-picked Instagram/YouTube — always use these
     first), (2) `candidates.bbc_phrases` (each episode title IS a real idiom/phrase) and
     `candidates.youtube` (latest uploads from everyday-English channels — the `title`/`description`
     usually name the target phrase; mine those), plus one of `candidates.bbc` / `lukes` (pick a
     *different* primary source than recent days, for variety). Use `candidates.tatoeba` for
     authentic example sentences (`text`, `url`). Candidates are seeds — prefer real, common usage over source rarity.
   - **Word lists for the `business` and `ielts` slots:** `candidates.tsl` (TOEIC words) seeds `business`,
     `candidates.nawl` (academic words) seeds `ielts`. Take **at least half** of each slot from its list,
     skipping any word the frequency test or exam-use rule above rejects. Teach the word in its usual
     collocation when it has one. Set `source` to `TSL` / `NAWL`. Each word carries real sentences in
     `tatoeba`: when one is natural and clear, use it as `example` word for word and set `source_url` to its
     `url` (that credits its author); otherwise write your own example and leave `source_url` null.
     Tatoeba is written by volunteers: never use a sentence that is sexual, violent, hateful or awkward.
   - The rest of those slots may come from your own knowledge of current workplace usage and IELTS
     band-7+ vocabulary: set `source` to `Claude` and leave `source_url` null. Only claim a real source
     when you actually used its material.
   - **SNS posts — EXTRA cards, on top of the 30:** `candidates.sns` lists English posts the user saved on
     Instagram/YouTube (`title`, `summary` = the user's Korean note, `tags`, and `text` = on-screen text +
     video transcript; the transcript is machine-made, so trust on-screen text over it). A post may be an
     English lesson or just a talk show, drama or vlog clip. Either way take what a learner can use: the
     expressions it teaches, or the natural spoken phrases people in it actually say (reactions, phrasal
     verbs, idioms, discourse markers) that pass the frequency test above — **up to 5 per post**, the most
     useful first. Skip a post with no usable English (music only, a meme with no line) and name it in your
     summary. Write your own `example` and `example2` rather than copying the post's sentence. Set `style`
     and `level` by the card itself, `source` to `Instagram` or `YouTube` (from `link`) and `source_url` to
     the post's `link` — that marks the post as used. Run them through step 3 like every pick; they do not
     count toward the 30.

   **Chinese (30 items, beginner — 기초부터):**
   - Use `candidates.hsk` words (already filtered to unused, frequency order) as the backbone;
     use `candidates.inbox` first if present. Each word carries real sentences in `tatoeba`: when one is
     simple enough for the level, use it as `example` word for word and set `source_url` to its `url`.
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
   - **SNS posts — EXTRA cards, on top of the 30:** `candidates.sns` lists Chinese-study posts the
     user saved on Instagram/YouTube (`title`, `summary`, `tags`, and `text` = on-screen text + video
     transcript; the transcript is machine-made, so trust the Chinese characters in `summary`/`text`
     over garbled 한글 sound-spellings). From each post take the expressions it actually teaches —
     **up to 5 per post**, the most useful first; skip a post that names no expression. Any level
     (not limited to `current_hsk_level`; set `level` to the closest `HSK1`–`HSK6`, or `HSK7-9` when the
     expression's hardest word is from the 7–9 band). Set `source` to
     `Instagram` or `YouTube` (from `link`) and `source_url` to the post's `link` — that is what marks
     the post as used. Run them through step 3 like every pick; they do not count toward the 30 and
     are not woven into the practice object.

   **Inbox items:** extract the single most useful expression from the link / `raw_text`; set
   `source` to `Instagram` or `YouTube` (based on the link), `source_url` to the link, and
   `inbox_page_id` to that row's `inbox_page_id` so the script marks it processed.

   **Pick before you write cards:** first choose the expressions only — about 1.5× the target
   (≈45 English, ≈45 Chinese) — then run step 3, and only expand the survivors into full cards.

3. **DEDUP (critical) — check your picks against everything already saved:**
   write the picked expressions as a JSON array of strings to `en_check.json` / `zh_check.json`, then run
   - `python daily_notion.py check en en_check.json`
   - `python daily_notion.py check zh zh_check.json`

   Each prints three lists:
   - `duplicates` — already saved (the `matches` show which). **Drop these.** The write step would
     skip them anyway.
   - `check_meaning` — not a string match, but shares a word with the saved expressions in
     `related`. **You decide:** drop it if it is the same expression in another form
     (take off / taking off / took off, pull your weight / pull one's weight) or a near-synonym /
     reworded version of one in `related`; keep it if it only shares an ordinary word.
   - `clear` — nothing close is saved. Keep.

   For `zh`, `check` also prints `dictionary`: the CC-CEDICT readings of each pick (`bei3 jing1` = běi jīng;
   5 = neutral tone). **Write `pronunciation` to agree with it.** Empty means a phrase the dictionary lacks.
   When you pick a word from the dictionary rather than HSK, set `source` to `CC-CEDICT`.

   Replace what you dropped with new picks and run `check` again on just the replacements, until
   you have the target count (or the frequency rule above says to write fewer).
   Your picks must also not repeat each other — `check` flags repeats inside the list as `duplicates`.

4. Expand the kept picks into the item objects and write the arrays to `en_items.json` and
   `zh_items.json` in the repo (UTF-8). Each card also gets its three **wrong options** for the quiz app
   (`options` in the schema below): read `docs/options.md` first and follow its rules.

5. Run: `python daily_notion.py write en_items.json zh_items.json`
   It adds each card to the database, makes its Notion backup page, marks processed inbox items, and posts
   the Discord summary. Report its output, including these lists when they are not empty:
   - `db_failed` — the database refused these cards, so they were not saved anywhere. Name them.
   - `backup_pending` — saved, but the Notion page failed; the app's daily job makes it. Just report.
   - `options_refused` — the card was saved without options; step 6 offers it again.

6. **Wrong options for cards that still have none** (earlier cards, and any refused in step 5). For `en`,
   then `zh`:
   - `python daily_notion.py missing-options <lang> 100` lists up to 100 cards with no options.
     If `cards` is empty, go to the next language.
   - Write `<lang>_options.json`: `[{"id": ..., "expression": ..., "options": [[expression, meaning] x3]}]`
     following `docs/options.md`, then run `python daily_notion.py add-options <lang>_options.json`.
     Rewrite the ones under `refused` and run `add-options` again on just those. Fix what `warnings` names
     when it is easy. A card that looks wrong in itself: leave it out and name it in your summary.

   The cards from step 5 are already saved. If this step fails, say so in your summary and stop; the next
   run picks up every card still without options.

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
  "level": "EN4",
  "usage_note": "새 일·역할을 빠르게 잘 시작한다는 뜻. 'start strong'보다 관용적.",
  "source": "BBC",
  "source_url": "https://www.bbc.co.uk/learningenglish",
  "inbox_page_id": null,
  "options": [
    ["to get off on the wrong foot", "처음부터 일이 꼬이다"],
    ["to drag one's feet", "일부러 꾸물거리며 미루다"],
    ["to jump the gun", "때가 되기 전에 성급하게 나서다"]
  ]
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
