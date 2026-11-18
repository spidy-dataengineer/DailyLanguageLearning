from content.card_check import check_card

CARD = {"expression": "fair enough", "level": "EN2", "usage_note": "상대 말을 받아들일 때 씀",
        "example": "Fair enough, let's go with your plan."}


def test_passes_a_clean_card():
    assert check_card(CARD, "en") is None


def test_refuses_editing_notes_and_field_labels_in_the_explanation():
    for note in ["뜻 설명 / 원래 예문: fair enuf lol", "원래 표기: fair enuf", "EN: reasonable / 받아들일 때", "받아들일 때 / 노트: 씀",
                 "종류: 구"]:
        assert "메모·틀 이름" in check_card({**CARD, "usage_note": note}, "en")
    assert check_card({**CARD, "usage_note": "ENGLISH 와 달리 씀"}, "en") is None


def test_refuses_an_empty_explanation_or_a_dash_in_the_example():
    assert "비어 있음" in check_card({**CARD, "usage_note": "  "}, "en")
    assert "줄표" in check_card({**CARD, "example": "Fair enough — let's go."}, "en")


def test_refuses_an_example_far_too_short_or_too_long():
    assert check_card({**CARD, "example": "Fair enough, then."}, "en") is None
    assert check_card({**CARD, "example": "Fair enough."}, "en") == "fair enough: 예문이 2단어 (3~30단어 밖)"
    assert check_card({**CARD, "example": " ".join(["word"] * 30)}, "en") is None
    assert "31단어" in check_card({**CARD, "example": " ".join(["word"] * 31)}, "en")
    zh = {"expression": "见", "level": "HSK1", "usage_note": "보다, 만나다", "example": "明天见！"}
    assert check_card(zh, "zh") is None
    assert check_card({**zh, "example": "再见！"}, "zh") == "见: 예문이 2자 (3~30자 밖)"
    assert "31자" in check_card({**zh, "example": "好" * 31}, "zh")
