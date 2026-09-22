"""Tests for srs.review.pick (daily review cap) and the webhook-safe error log in notify._post."""
import requests

import notify.notify as n
from srs.review import pick


def _row(expr, nxt="2026-09-22", created="2026-09-01", recall=None):
    return {"expression": expr, "next": nxt, "created": created, "recall": recall}


def test_cap_takes_longest_waiting_unmarked_cards():
    rows = [_row("new", "2026-09-22", "2026-09-21"), _row("old", "2026-09-10", "2026-09-01"),
            _row("never-scheduled", None, "2026-08-01"), _row("mid", "2026-09-15", "2026-09-05")]
    assert [r["expression"] for r in pick(rows, 2)] == ["never-scheduled", "old"]


def test_same_due_date_breaks_tie_by_oldest_card():
    rows = [_row("b", created="2026-09-02"), _row("a", created="2026-09-01"), _row("c", created="2026-09-03")]
    assert [r["expression"] for r in pick(rows, 2)] == ["a", "b"]


def test_marked_cards_always_processed_even_past_the_cap():
    rows = [_row("x", recall="Forgot"), _row("y", recall="Got it"), _row("z", recall="Forgot"),
            _row("waiting", "2026-01-01")]
    assert [r["expression"] for r in pick(rows, 2)] == ["x", "y", "z"]


def test_webhook_error_log_never_contains_the_url(capsys, monkeypatch):
    url = "https://discord.com/api/webhooks/123/SECRET-TOKEN"
    resp = requests.Response()
    resp.status_code = 429

    class R:
        def raise_for_status(self):
            raise requests.HTTPError(f"429 Client Error: Too Many Requests for url: {url}", response=resp)

    monkeypatch.setattr(n.requests, "post", lambda *a, **k: R())
    n._post(url, ["hello"], "review ping")
    err = capsys.readouterr().err
    assert "429" in err and "SECRET-TOKEN" not in err
