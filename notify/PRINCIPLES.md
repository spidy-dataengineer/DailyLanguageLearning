# notify/ — Discord notifications (principles)

`notify.py`: three one-way Discord webhook pings — daily write summary, SRS review, stats.

- **One-way only**: feedback never flows back through Discord — it flows through Notion `Recall`.
- Never print/post the webhook URL; skip silently if `DISCORD_WEBHOOK_URL` is unset.
- Meanings are hidden as `||spoilers||` in the review ping (active recall); each message caps at ~1990 chars.

Detail → [../docs/notify.md](../docs/notify.md)
