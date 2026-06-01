# Migration → personal PC → GitHub `/schedule`

Goal: move the whole project off the work machine to your **personal PC**, then push to a **private
GitHub repo** and schedule the daily routine. **Do NOT push to GitHub from the work machine** — move
files via USB / personal cloud, and push only from the personal PC.

## What moves
The entire `notion/` folder **except** `.venv/`, `.idea/`, `__pycache__/` (those regenerate). That
includes all code + every doc:
- Code: `daily_notion.py`, `sources.py`
- Config: `requirements.txt`, `.env.example`, `.gitignore`
- Docs: `README.md`, `CLAUDE.md`, `routine_prompt.md`, `MIGRATION.md`, `docs/*.md` (overview, sources,
  notion, dedup, generation, deployment, review, **plan**)
- `data/` (Tatoeba subset, if you add one)
- `.env` — your secrets; handle separately (Step 2)

> The Notion databases live in **your Notion account (cloud)** — they're already there and don't need
> to move. The personal PC just needs the `.env` with the token + DB IDs to reach them.

## Step 1 — Stage a clean copy on this PC
Either use the prepared **`notion-project.zip`** (in your home folder `C:\Users\JimmyPark\`; it already
excludes `.venv/.idea/__pycache__/.env`), **or** copy manually to a USB drive (here `E:`):
```
robocopy "C:\Users\JimmyPark\IdeaProjects\notion" "E:\notion" /E /XD .venv .idea __pycache__ /XF *.pyc
```
Put the zip (or the `E:\notion` folder) on a **USB drive** and carry it home.

## Step 2 — Your secrets (`.env`)
The zip leaves out `.env` (it holds your Notion token + Discord webhook). On the personal PC, copy
`.env.example` to `.env` and fill these — the DB IDs are below, the two secrets you copy from your
current `.env` (open it on this PC and copy the values):
```
NOTION_TOKEN=<copy from your current .env>
NOTION_DB_ID_EN=44c740ac-fc94-4b3b-80e3-391d92a9409b
NOTION_DB_ID_ZH=9e140efe-bf67-41c2-8de5-90c583267dee
NOTION_DB_ID_INBOX=973db572-2ee6-4476-b18c-21e40e318e39
DISCORD_WEBHOOK_URL=<copy from your current .env>
```
(Or just copy the `.env` file itself to the USB too — it's tiny. Never commit it; `.gitignore`
already excludes it.)

## Step 3 — Set up on the personal PC
1. Install **Python 3.13**, **Git**, and **Claude Code**; run `claude` and log in with your **Max** account.
2. In the project folder:
   ```
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```
3. Smoke test: `python daily_notion.py fetch en` — should print candidate JSON (uses your `.env`).

## Step 4 — Private GitHub repo (on the personal PC)
```
gh auth login                      # one-time
git init
git add .
git status                         # CONFIRM .env is NOT listed (it's gitignored)
git commit -m "Daily bilingual expression logger"
gh repo create notion-daily --private --source . --push
```

## Step 5 — Schedule the daily routine (`/schedule`)
In Claude Code on the personal PC, run `/schedule`:
- Point it at the `notion-daily` repo.
- Set env vars (from your `.env`): `NOTION_TOKEN`, `NOTION_DB_ID_EN/ZH/INBOX`, `DISCORD_WEBHOOK_URL`.
- Prompt = the contents of `routine_prompt.md`.
- Daily time (e.g. 08:00; minimum interval 1h).
- Do a **one-off run** to verify: it should `review` → generate 10 EN + 10 ZH → `write` → Discord ping.

## After deployment — remaining enhancements
Increments 2–4 (pronunciation audio, cloze + reverse cards, stats) are specced in `docs/plan.md`
and the `docs/overview.md` roadmap. Build them on the personal PC, updating the matching `docs/`
file per the working rules in `CLAUDE.md`.

## Optional — Claude's session memory
This session's notes live at `~/.claude/projects/<project>/memory/` (MEMORY.md + notes). Not needed
to run the project; copy that folder to the personal PC's `~/.claude/...` only if you want a future
Claude session to keep the build history.
