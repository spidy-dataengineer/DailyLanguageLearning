from content.options_check import check_options

CARD = {"expression": "to cut corners", "meaning_ko": "(돈·시간을 아끼려고) 대충 하다, 절차를 생략하다",
        "example": "Don't cut corners on safety."}
GOOD = [["to cut costs", "비용을 줄이다"], ["to turn the corner", "고비를 넘기다"], ["to go the extra mile", "기대 이상으로 노력하다"]]


def test_passes_three_plausible_options():
    assert check_options(CARD, GOOD) == (None, [])


def test_refuses_anything_but_three_pairs():
    assert "3개가 아님" in check_options(CARD, GOOD[:2])[0]
    assert "3개가 아님" in check_options(CARD, GOOD[:2] + [["x", ""]])[0]
    assert "3개가 아님" in check_options(CARD, None)[0]


def test_refuses_an_option_that_is_the_answer_or_a_repeat():
    assert "겹치거나 중복" in check_options(CARD, [["cut corners", "줄이다"]] + GOOD[1:])[0]
    assert "겹치거나 중복" in check_options(CARD, [GOOD[0], GOOD[0], GOOD[2]])[0]


def test_refuses_a_meaning_the_answer_already_has():
    assert "뜻이 정답과 겹침" in check_options(CARD, [["to skip steps", "대충 하다"]] + GOOD[1:])[0]
    assert "뜻이 정답과 겹침" in check_options(CARD, [["to rush", "생략하다"]] + GOOD[1:])[0]


def test_refuses_a_meaning_a_question_would_cut_short():
    assert "쉼표" in check_options(CARD, [["to cut costs", "비용을 줄이다, 아끼다"]] + GOOD[1:])[0]
    assert "쉼표" in check_options(CARD, [["to cut costs", "① 줄이다"]] + GOOD[1:])[0]


def test_warns_but_keeps_short_options_and_a_wrong_article():
    card = {"expression": "an uphill battle", "meaning_ko": "많은 노력이 필요한 아주 힘든 싸움", "example": "It was an uphill battle."}
    problem, warnings = check_options(card, [["a dead end", "막다른 길"], ["a long shot", "희박한 가능성"], ["a close call", "아슬아슬한 순간"]])
    assert problem is None
    assert any("8자 이상 짧음" in w for w in warnings)
    card = {"expression": "apple", "meaning_ko": "사과", "example": "I ate an apple."}
    problem, warnings = check_options(card, [["pear", "배"], ["orange", "오렌지"], ["egg", "달걀"]])
    assert problem is None and warnings == ["apple: an 뒤에 pear"]
