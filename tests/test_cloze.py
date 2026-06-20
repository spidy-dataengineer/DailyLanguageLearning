"""Tests for notion.notion_io.cloze (active-recall blanking)."""
from notion.notion_io import cloze


def test_blanks_expression_verbatim():
    assert cloze("Let's call it a day.", "call it a day") == "Let's ____."


def test_case_insensitive():
    assert cloze("CALL IT A DAY now.", "call it a day") == "____ now."


def test_fail_soft_when_absent():
    s = "This sentence lacks the phrase."
    assert cloze(s, "rain check") == s


def test_empty_inputs():
    assert cloze("", "x") == ""
    assert cloze("hello", "") == "hello"
