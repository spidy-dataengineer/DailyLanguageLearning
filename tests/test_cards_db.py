import datetime as dt

from db import cards_db


def test_card_row_holds_everything_the_backup_page_has():
    item = {"expression": " spot me a few bucks ", "meaning_ko": "돈 좀 빌려줘", "example": "Can you spot me a few bucks?",
            "example_ko": "몇 달러만 빌려줄래?", "example2": "I'll spot you.", "example2_ko": "내가 내줄게.",
            "pronunciation": "/spɑt mi/", "usage_note": "친구끼리", "style": "slang", "level": "EN5",
            "source": "Instagram", "source_url": "https://www.instagram.com/p/x/"}
    row = cards_db.card_row(item, "en", [["a", "b"]] * 3, None, dt.date(2026, 11, 10))
    assert row == {
        "lang": "en", "expression": "spot me a few bucks", "meaning_ko": "돈 좀 빌려줘",
        "example": "Can you spot me a few bucks?", "example_ko": "몇 달러만 빌려줄래?",
        "example2": "I'll spot you.", "example2_ko": "내가 내줄게.", "pronunciation": "/spɑt mi/",
        "usage_note": "친구끼리", "style": "slang", "level": "EN5", "origin": "Instagram",
        "source_url": "https://www.instagram.com/p/x/", "audio_url": None, "added_on": "2026-11-10",
        "options": [["a", "b"]] * 3,
    }


def test_card_row_drops_a_style_the_app_does_not_know_and_fills_blanks():
    row = cards_db.card_row({"expression": "你好", "style": "made-up"}, "zh", None, "https://x/a.mp3", dt.date(2026, 11, 10))
    assert row["style"] == "" and row["example2"] == "" and row["origin"] == "" and row["options"] is None
    assert row["audio_url"] == "https://x/a.mp3"


def test_sends_the_key_only_when_this_machine_has_one(monkeypatch):
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    assert "apikey" not in cards_db._headers()  # the cloud environment adds it on the way out
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "local-key")
    assert cards_db._headers("return=minimal") == {
        "Content-Type": "application/json", "apikey": "local-key", "Prefer": "return=minimal"}
