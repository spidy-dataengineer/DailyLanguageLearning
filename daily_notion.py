"""Daily bilingual language-learning routine: Notion (REST) + Discord — CLI entry point.

Modes:
  python daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]   # create the 3 databases
  python daily_notion.py fetch <en|zh>                                    # gather raw material -> JSON on stdout
  python daily_notion.py write <en_items.json> <zh_items.json>            # create rows + notify
  python daily_notion.py review                                           # SRS: surface due cards, reschedule
  python daily_notion.py stats                                            # read-only aggregates -> JSON + Discord
  python daily_notion.py migrate                                          # ensure SRS properties on existing DBs

Python only does I/O (gather + write). The /schedule routine's own Claude reasoning turns the
fetched raw material into the day's items (see routine_prompt.md). Code is split by concern:
  notion_io.py — Notion API + schema/init + page layout + audio + fetch + write
  dedup.py     — similarity-based duplicate detection + HSK progression
  review.py    — SRS (spaced repetition) review logic
  stats.py     — read-only aggregates
  notify.py    — Discord webhook senders
  sources.py   — external source fetchers (MW, BBC, Luke's, HSK, Tatoeba)
  constants.py — shared constants
"""
from __future__ import annotations

import sys

from notion_io import fetch, init, migrate, write
from review import review
from stats import stats


def main(argv) -> None:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp949; force UTF-8
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2:
        raise SystemExit(__doc__)
    cmd = argv[1]
    if cmd == "init":
        if len(argv) < 4:
            raise SystemExit("usage: daily_notion.py init <en_page_id> <zh_page_id> [inbox_page_id]")
        init(argv[2], argv[3], argv[4] if len(argv) > 4 else None)
    elif cmd == "fetch":
        if len(argv) < 3:
            raise SystemExit("usage: daily_notion.py fetch <en|zh>")
        fetch(argv[2])
    elif cmd == "migrate":
        migrate()
    elif cmd == "review":
        review()
    elif cmd == "stats":
        stats()
    elif cmd == "write":
        write(argv[2] if len(argv) > 2 else None, argv[3] if len(argv) > 3 else None)
    else:
        raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main(sys.argv)
