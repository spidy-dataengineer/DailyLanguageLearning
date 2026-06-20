"""Tests for the dedup safety net (content.dedup)."""
from content.dedup import norm, similar, similar_to_any


def test_norm_lowercases_and_strips_punct():
    assert norm("  Read the Room!! ") == "read the room"


def test_similar_exact_and_case_variant():
    assert similar("no worries", "no worries")
    assert similar("call it a day", "Call it a day.")


def test_similar_whole_phrase_containment():
    assert similar("rain check", "take a rain check")


def test_similar_distinct_expressions():
    assert not similar("read the room", "call it a day")


def test_similar_to_any():
    pool = ["fair enough", "read the room"]
    assert similar_to_any("Read the room!", pool)
    assert not similar_to_any("touch base", pool)
