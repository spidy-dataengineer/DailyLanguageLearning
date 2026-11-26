import datetime as dt
import json

from content.options_check import option_key
from db import cards_db
from notion import notion_io

CARD = {"id": "c1", "lang": "en", "level": "EN2", "style": "everyday", "expression": "on earth",
        "meaning_ko": "도대체", "example": "What on earth is this?", "example_ko": "이게 도대체 뭐야?",
        "example2": "", "example2_ko": "", "usage_note": "의문사를 강조해 '도대체'",
        "options": [["else", "그 밖에 또"], ["exactly", "정확히"], ["kind of", "어떤 종류의"]],
        "content_flag": None, "updated_at": "2026-11-24T23:10:00.12345+00:00"}


def test_reads_database_times_with_any_number_of_second_digits():
    assert cards_db._when("2026-11-25T00:40:12.12345+00:00") == dt.datetime(2026, 11, 25, 0, 40, 12, 123450, dt.timezone.utc)
    assert cards_db._when("2026-11-25T00:40:12Z") == dt.datetime(2026, 11, 25, 0, 40, 12, tzinfo=dt.timezone.utc)


def test_lists_only_fails_nobody_fixed_after_the_review(monkeypatch):
    fails = [
        {"card_id": "c1", "rule": "오답-03", "reason": "끝맺음이 섞임", "reviewed_at": "2026-11-25T00:40:00+00:00"},
        {"card_id": "c1", "rule": "설명-02", "reason": "전문 용어", "reviewed_at": "2026-11-25T00:40:00+00:00"},
        {"card_id": "c2", "rule": "오답-05", "reason": "주제 밖", "reviewed_at": "2026-11-24T00:40:00+00:00"},
    ]
    fixed_since = {**CARD, "id": "c2", "updated_at": "2026-11-24T09:00:00+00:00"}
    monkeypatch.setattr(cards_db, "_get_all", lambda table, params: fails if table == "card_reviews" else [CARD, fixed_since])
    out = cards_db.flagged_cards(dt.datetime(2026, 11, 22, tzinfo=dt.timezone.utc))
    assert [c["id"] for c in out] == ["c1"]
    assert out[0]["fails"] == [{"rule": "오답-03", "reason": "끝맺음이 섞임"}, {"rule": "설명-02", "reason": "전문 용어"}]


def run_fix(monkeypatch, tmp_path, capsys, entries, updated=True, dry_run=False):
    writes = []
    monkeypatch.setattr(cards_db, "cards_full", lambda ids: {"c1": dict(CARD)})
    # The database count includes this card's own options.
    monkeypatch.setattr(cards_db, "option_uses", lambda lang: {option_key(o): 1 for o, _ in CARD["options"]})
    monkeypatch.setattr(cards_db, "update_card", lambda *a: writes.append(a) or updated)
    path = tmp_path / "fixes.json"
    path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    notion_io.fix_cards(str(path), dry_run)
    return json.loads(capsys.readouterr().out), writes


def test_writes_only_the_changed_fields_and_shows_them_before_and_after(monkeypatch, tmp_path, capsys):
    options = [["else", "그 밖에 또"], ["exactly", "정확히"], ["at all", "조금도"]]
    out, writes = run_fix(monkeypatch, tmp_path, capsys, [{"id": "c1", "expression": "on earth", "options": options,
                                                           "meaning_ko": "도대체"}])
    assert out["refused"] == []
    assert writes == [("c1", "on earth", {"options": options})]
    assert out["fixed"] == [{"expression": "on earth", "before": {"options": CARD["options"]}, "after": {"options": options}}]


def test_refuses_what_the_morning_job_may_not_change_or_what_breaks_a_rule(monkeypatch, tmp_path, capsys):
    out, writes = run_fix(monkeypatch, tmp_path, capsys, [
        {"id": "c1", "expression": "on earth", "level": "EN3"},
        {"id": "c1", "expression": "in earth", "usage_note": "다른 설명"},
        {"id": "c1", "expression": "on earth", "usage_note": "노트: 원래 메모"},
        {"id": "c1", "expression": "on earth", "content_flag": "rude"},
        {"id": "c1", "expression": "on earth", "meaning_ko": "도대체"},
    ])
    assert writes == []
    assert out["refused"] == [
        "on earth: 여기서 못 고치는 칸 (level)",
        "in earth: 카드가 없거나 표현이 바뀜",
        "on earth: 설명에 메모·틀 이름 (노트:)",
        "on earth: content_flag 는 vulgar, sexual, null 중 하나",
        "on earth: 바뀐 칸 없음",
    ]


def test_says_so_when_the_card_changed_while_writing(monkeypatch, tmp_path, capsys):
    out, _ = run_fix(monkeypatch, tmp_path, capsys, [{"id": "c1", "expression": "on earth", "usage_note": "의문사 뒤에서 '도대체'"}],
                     updated=False)
    assert out["fixed"] == [] and out["refused"] == ["on earth: 쓰는 사이 표현이 바뀜"]


def test_a_dry_run_checks_and_shows_the_change_without_writing(monkeypatch, tmp_path, capsys):
    out, writes = run_fix(monkeypatch, tmp_path, capsys, [{"id": "c1", "expression": "on earth", "usage_note": "의문사 뒤에서 '도대체'"}],
                          dry_run=True)
    assert writes == [] and out["dry_run"] is True
    assert out["fixed"] == [{"expression": "on earth", "before": {"usage_note": CARD["usage_note"]},
                             "after": {"usage_note": "의문사 뒤에서 '도대체'"}}]
