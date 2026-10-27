"""Tests for the dedup safety net (content.dedup)."""
from content.dedup import check_candidates, norm, similar, similar_to_any


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


def test_check_candidates_splits_duplicates_related_and_clear():
    existing = ["read the room", "take off", "fair enough", "call it a day"]
    out = check_candidates(["Read the room!", "taking off", "touch base", "fair enough"], existing)
    assert out["duplicates"] == [
        {"candidate": "Read the room!", "matches": ["read the room"]},
        {"candidate": "fair enough", "matches": ["fair enough"]},
    ]
    # a morphological variant is not a string duplicate, so it comes back for Claude to judge
    assert out["check_meaning"] == [{"candidate": "taking off", "related": ["take off"]}]
    assert out["clear"] == ["touch base"]


def test_check_candidates_catches_repeats_inside_the_list():
    out = check_candidates(["touch base", "Touch base."], [])
    assert out["duplicates"] == [{"candidate": "Touch base.", "matches": ["touch base"]}]
    assert out["clear"] == ["touch base"]


def test_check_candidates_ignores_common_words():
    out = check_candidates(["on the fence"], ["on the go", "in the loop"])
    assert out["clear"] == ["on the fence"]


def test_check_candidates_chinese_shares_characters():
    out = check_candidates(["爱好", "图书馆"], ["我的爱好", "电脑"])
    assert out["duplicates"] == []
    assert out["check_meaning"] == [{"candidate": "爱好", "related": ["我的爱好"]}]
    assert out["clear"] == ["图书馆"]
