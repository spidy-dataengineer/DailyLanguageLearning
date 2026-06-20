# notion/ — Notion gateway (principles)

`notion_io.py` is the **only** module that talks to Notion's REST API (client, schema, init/migrate,
page layout, audio URLs, fetch, write).

- Use the **2025-09-03 data-source model**: `data_sources.query` / `pages.create(parent=data_source_id)`;
  resolve with `data_source_id(db_id)`.
- **Python does I/O only** — no language generation here (that's the `/schedule` routine's Claude).
- English & Chinese live in **separate DBs**; never mix in one entry.
- Adding a card property: define it in `_EXPR_SCHEMA_BASE`, set it in `_properties`, and add it to
  `migrate` so existing DBs get the column. **migrate-before-write** — Notion auto-creates select
  *options* but never the *property* itself, so an un-migrated `write` fails.
- Secrets/DB IDs come from `.env`; never print the token/webhook.

Detail → [../docs/notion.md](../docs/notion.md) · inbox → [../docs/inbox.md](../docs/inbox.md)
