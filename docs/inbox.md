# Inbox (manual ingestion + auto-source roadmap)

The **Language Inbox** Notion DB is the channel for feeding *specific* expressions you found
yourself (a reel, a video, an article) into the daily run so they become cards.

Code: `notion_io.inbox_unprocessed` (read, called in `fetch`) + the processed-flag flip in
`notion_io.write`. Schema created by `init` (`_INBOX_SCHEMA`). The routine's prompt handles the
extraction (see the "Inbox items" rule in `routine_prompt.md`).

## How it works — one-time, no recurring load
Fields: `Item`(title) · `Link`(url) · `Raw text` · `Language`(select En/Zh) · `Note` · `Processed`(checkbox) · `Added`(date).

1. You add a row (leave `Processed` unchecked).
2. The next run's `fetch` queries **only `Processed=false`** rows for that language → passes them
   to the routine as `candidates.inbox` (used **first**, top priority).
3. `write` creates the card(s) and flips that row's `Processed=true`.
4. Every later run's query **excludes** it → it is never read or re-processed again.

So each row is processed **exactly once**. There is **no repeated parsing and no recurring load**,
and the routine never fetches the linked video at all (see next). Verified end-to-end 2026-06-03.

## The link is stored, NOT fetched
The cloud routine **cannot open** an Instagram / YouTube / arbitrary URL:
- Instagram has no public API + a login wall; YouTube transcripts are blocked from datacenter IPs;
- the routine has no web-fetch tool and runs under a network allowlist (only the configured feed/API hosts).

So `Link` is only **stored as the card's `source_url`** (a reference string). **The content that
becomes the card comes from what you paste into `Raw text`.** A bare reel URL returns nothing
fetchable — confirmed by test: the card *"Can I get this to-go?"* was built from its `Raw text`,
with the IG URL recorded as source only.

→ For Instagram/YouTube, **put the expression (or caption / subtitle text) in `Raw text`.**
The URL alone is not enough — "giving the URL" records the source, it does not pull the content.

## Roadmap — auto-collection (follow a creator, no hunting)
To pull a creator's new uploads automatically, add them as a **recurring source** — same pattern
as BBC "The English We Speak" ([sources](sources.md)): a fetcher in `sources.py` + the host in the
environment's network allowlist + a mention in `routine_prompt.md`.

| Source type | Auto from cloud? | How |
|---|---|---|
| **YouTube channel** | ✅ **(implemented)** | `sources.youtube_channels()` reads `sources.YT_CHANNELS` (name→channel_id) → each new upload's **title + description** via per-channel RSS `youtube.com/feeds/videos.xml?channel_id=…` (not the transcript — cloud-IP blocked; but learning-channel titles/descriptions usually carry the phrase). Needs `youtube.com` in the network allowlist. Add/remove channels by editing `YT_CHANNELS`. |
| **Podcast / blog / Substack (has RSS)** | ✅ | add a fetcher like `bbc_the_english_we_speak()` + allowlist the host. |
| **Instagram / TikTok creator** | ❌ | no API / login wall / IP block. Only via a **PC-side** tool (e.g. `yt-dlp`) that writes Inbox rows while your PC is on. |

Auto-sources feed `candidates` (seeds), exactly like MW/BBC/Tatoeba; the **Inbox stays the channel
for one-off manual picks**. The two coexist.
