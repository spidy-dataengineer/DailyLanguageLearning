# Notion (schema & layout)

Uses the **2025-09-03 data-source model** (notion-client 3.1.0 default): create a DB with
`initial_data_source`; query/write via `data_sources.query` / `pages.create(parent=data_source_id)`.
`daily_notion.data_source_id(db_id)` resolves the data source via `databases.retrieve`. DB IDs live in `.env`.

## Databases (3)
- **English Expressions** (under the EN page) and **Chinese Expressions** (under the ZH page) — kept separate.
- **Language Inbox** — manual Instagram/YouTube drop queue.

Created by `python daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]`.

## Expression schema (EN & ZH share structure)
`Expression`(title) · `Meaning (KO)` · `Example` · `Example (KO)` · `Pronunciation` ·
`Style`(select) · `Level`(select: `EN-advanced` / `HSK1`–`HSK6`) · `Usage note` ·
`Source`(select) · `Source URL`(url) · `Date` · `Audio`(url, v1 empty) ·
`Box`(number) · `Next review`(date) · `Recall`(select: Got it/Forgot — the only field you mark) · `Last reviewed`(date) → SRS, see [review](review.md)

## Inbox schema
`Item`(title) · `Link`(url) · `Raw text` · `Language`(select) · `Note` · `Processed`(checkbox) · `Added`(date)

## Flashcard page body (built in `write` → `_page_body`)
Each row's page: 💬 example (callout) → **`👀 뜻 보기` toggle** (hides meaning + KO translation =
active recall) → 🔊 pronunciation → 📝 usage note → 🔗 source. Page icon = 🇬🇧 / 🇨🇳.

## Chinese daily practice (`_write_practice`)
One extra row per day: **`📝 오늘의 연습 · <date>`** (icon ✍️) — 3–4 simple sentences weaving the
day's words, each a toggle (zh + pinyin visible, KO hidden). Comes from a
`{"type":"practice","sentences":[{zh,pinyin,ko}…]}` object at the end of the ZH array.

## Tips
- Switch each DB to a **Gallery view** in Notion for card-style browsing.
- Deleting rows = archive via `pages.update(archived=True)` (recoverable in Notion trash).
