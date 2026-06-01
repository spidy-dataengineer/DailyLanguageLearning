# Deployment / scheduling

## Decision
Run unattended daily with the **PC possibly off** → Claude Code **cloud routine (`/schedule`)**,
using the Max subscription (no API key). Code reaches the cloud via a **private GitHub repo** the
routine clones each run.

**Deferred to a PERSONAL PC at home.** The user will **not** push from the work machine (company
monitoring/policy concern); covert workarounds were declined. Plan:
1. Copy the project folder + `.env` to a personal computer.
2. Push to a **private GitHub repo** there.
3. `/schedule`: point at the repo, set env vars from `.env`, paste `routine_prompt.md` as the prompt,
   pick a daily time (min interval 1h). Verify with a one-off run.

## Alternatives (no GitHub)
- **Local Windows Task Scheduler + `claude -p`** — no GitHub, no API key (uses Max); but PC must be **ON** at run time.
- **Cloud service + Anthropic API key** (Modal / Railway / cloud functions) — PC off, no GitHub; small API cost, separate from Max.

## Remaining setup checklist
- [x] Notion integration + 3 DBs + `.env` DB IDs
- [x] Discord webhook + notify verified
- [ ] Personal PC: copy project → private GitHub repo → `/schedule`
