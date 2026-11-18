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


def test_refuses_options_all_much_shorter_than_the_answer():
    card = {"expression": "an uphill battle", "meaning_ko": "많은 노력이 필요한 아주 힘든 싸움", "example": "It was an uphill battle."}
    assert "많이 짧음" in check_options(card, [["a dead end", "막다른 길"], ["a long shot", "희박한 가능성"], ["a close call", "아슬아슬한 순간"]])[0]
    assert check_options(card, [["a dead end", "더 나아갈 수 없는 막다른 길"], ["a long shot", "희박한 가능성"], ["a close call", "아슬아슬한 순간"]])[0] is None
    long = {"expression": "to take something for granted", "meaning_ko": "당연하게 여기다", "example": "We take water for granted."}
    assert "표현이 다 정답보다" in check_options(long, [["to sit", "의자에 앉아 있다"], ["to go", "멀리 가 버리다"], ["to see", "가만히 보고 있다"]])[0]


def test_refuses_options_all_padded_longer_than_the_answer():
    card = {"expression": "literally", "meaning_ko": "말 그대로", "example": "I literally have no idea."}
    padded = [["still", "아직도 계속해서"], ["sometimes", "때때로 이따금씩"], ["usually", "보통 대개의 경우에"]]
    assert "많이 김" in check_options(card, padded)[0]
    assert check_options(card, [["still", "아직도"], ["sometimes", "때때로"], ["usually", "보통 대개는"]])[0] is None
    assert check_options(card, [["still", "아직도 여전히"], ["sometimes", "가끔 가다"], ["usually", "보통 대개는"]])[0] is None


def test_refuses_an_option_already_on_too_many_cards():
    card = {"expression": "医生", "meaning_ko": "의사", "example": "他是医生。"}
    options = [["老师", "선생님"], ["学生", "학생"], ["护士", "간호사"]]
    assert check_options(card, options, {"老师": 7}, "zh")[0] is None
    assert "이미 8장의 오답" in check_options(card, options, {"老师": 8}, "zh")[0]
    assert "이미 5장의 오답" in check_options(CARD, GOOD, {"to cut costs": 5}, "en")[0]
    assert check_options(CARD, GOOD, {"to cut costs": 4}, "en")[0] is None


def test_warns_but_keeps_a_wrong_article():
    card = {"expression": "apple", "meaning_ko": "사과", "example": "I ate an apple."}
    problem, warnings = check_options(card, [["pear", "배"], ["orange", "오렌지"], ["egg", "달걀"]])
    assert problem is None and warnings == ["apple: an 뒤에 pear"]
