"""Tests for notify.notify._chunks (splitting long pings under Discord's 2000-char cap)."""
from notify.notify import _LIMIT, _chunks


def test_short_ping_is_one_message():
    lines = ["📚 **오늘의 표현**", "", "• **fair enough** — 그럴 만하네"]
    assert _chunks(lines) == ["\n".join(lines)]


def test_long_ping_splits_between_lines_and_keeps_every_line():
    lines = [f"• **expression {i}** — 뜻 {i} " + "x" * 60 for i in range(40)]
    out = _chunks(lines)
    assert len(out) > 1
    assert all(len(c) <= _LIMIT for c in out)
    assert [l for c in out for l in c.split("\n")] == lines


def test_single_oversized_line_is_truncated():
    out = _chunks(["y" * (_LIMIT + 500)])
    assert out == ["y" * _LIMIT]
