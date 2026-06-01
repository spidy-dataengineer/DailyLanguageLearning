# Notion (schema & layout)

Code: `notion_io.py` (everything Notion: client + schema + init/migrate + page layout + audio + fetch + write).

Uses the **2025-09-03 data-source model** (notion-client 3.1.0 default): create a DB with
`initial_data_source`; query/write via `data_sources.query` / `pages.create(parent=data_source_id)`.
`notion_io.data_source_id(db_id)` resolves the data source via `databases.retrieve`. DB IDs live in `.env`.

## Databases (3)
- **English Expressions** (under the EN page) and **Chinese Expressions** (under the ZH page) — kept separate.
- **Language Inbox** — manual Instagram/YouTube drop queue.

Created by `python daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]`.

## Expression schema (EN & ZH share structure)
`Expression`(title) · `Meaning (KO)` · `Example` · `Example (KO)` · `Pronunciation` ·
`Style`(select) · `Level`(select: `EN-advanced` / `HSK1`–`HSK6`) · `Usage note` ·
`Source`(select) · `Source URL`(url) · `Date` · `Audio`(url — ZH: native recording (audio-cmn mp3 → Wikimedia Commons ogg), else a YouGlish link; EN empty for now) ·
`Box`(number) · `Next review`(date) · `Recall`(select: Got it/Forgot — the only field you mark) · `Last reviewed`(date) → SRS, see [review](review.md)

## Inbox schema
`Item`(title) · `Link`(url) · `Raw text` · `Language`(select) · `Note` · `Processed`(checkbox) · `Added`(date)

## Flashcard page body (built in `write` → `_page_body`)
Each row's page: 💬 **cloze** example (callout, the expression blanked to `____`; full sentence shown
only when the blank succeeded) → **`👀 뜻 보기` toggle** (reveals meaning + full example + KO translation
= active recall) → **`🔄 거꾸로 (뜻→표현)` toggle** (meaning in the label, expression hidden inside =
reverse recall) → 🔊 pronunciation → (ZH only) **inline native-audio block** + source credit (audio-cmn or
Wikimedia Commons), or a **🔊 발음 듣기** YouGlish link when no recording exists → 📝 usage note → 🔗 source.
Page icon = 🇬🇧 / 🇨🇳. Cloze falls back to the unchanged sentence (fail-soft) if the expression isn't found verbatim.

## Chinese daily practice (`_write_practice`)
One extra row per day: **`📝 오늘의 연습 · <date>`** (icon ✍️) — 3–4 simple sentences weaving the
day's words, each a toggle (zh + pinyin visible, KO hidden). Comes from a
`{"type":"practice","sentences":[{zh,pinyin,ko}…]}` object at the end of the ZH array.

## Tips
- Switch each DB to a **Gallery view** in Notion for card-style browsing.
- Deleting rows = archive via `pages.update(archived=True)` (recoverable in Notion trash).
