"""Tests for content.sources._readings (HSK dictionary entries -> learner-facing readings).

Fixtures are real entries from drkameleon/complete-hsk-vocabulary (HSK 2.0 exclusive lists).
"""
from content.sources import _readings


def _f(pinyin, *meanings):
    return {"transcriptions": {"pinyin": pinyin}, "meanings": list(meanings)}


def test_drops_surname_and_keeps_both_real_readings():
    jiao = [_f("Jué", "surname Jue"), _f("jiǎo", "angle", "corner"), _f("jué", "role (theater)", "to compete")]
    assert _readings(jiao) == [
        {"pinyin": "jiǎo", "meanings": ["angle", "corner"]},
        {"pinyin": "jué", "meanings": ["role (theater)", "to compete"]},
    ]


def test_drops_country_abbr_legend_and_variant_entries():
    ke = [_f("Kè", "abbr. for 克罗地亚, Croatia"), _f("kè", "to be able to", "to subdue"),
          _f("Kè", "Ke (c. 2000 BC), seventh of the legendary Flame Emperors"),
          _f("kè", "variant of 克", "to subdue"), _f("kè", "variant of 克")]
    assert _readings(ke) == [{"pinyin": "kè", "meanings": ["to be able to", "to subdue"]}]


def test_drops_cross_references():
    jia = [_f("gēi", "used in 掰"), _f("jiǎ", "fake", "false"), _f("jià", "vacation"),
           _f("jiǎ", "variant of 假", "to borrow")]
    assert [r["pinyin"] for r in _readings(jia)] == ["jiǎ", "jià"]
    assert _readings([_f("jiē", "see 节骨眼"), _f("jié", "joint", "node")]) == [
        {"pinyin": "jié", "meanings": ["joint", "node"]}]


def test_proper_noun_or_erhua_only_word_is_kept():
    # 北京 / 好玩儿 have nothing but a "junk-looking" entry — that entry IS the word.
    assert _readings([_f("Běi jīng", "Beijing")]) == [{"pinyin": "Běi jīng", "meanings": ["Beijing"]}]
    assert _readings([_f("hǎo wán r", "erhua variant of 好玩")]) == [
        {"pinyin": "hǎo wán r", "meanings": ["erhua variant of 好玩"]}]


def test_same_pinyin_entries_merge_without_losing_the_later_core_sense():
    hou = [_f("Hòu", "surname Hou"), _f("hòu", "empress", "queen", "(archaic) monarch", "ruler"),
           _f("hòu", "back", "behind", "rear", "afterwards", "after", "later", "post-")]
    r = _readings(hou)
    assert [x["pinyin"] for x in r] == ["hòu"]
    assert {"back", "behind"} <= set(r[0]["meanings"])


def test_meanings_capped_at_six_keeping_core_sense_of_a_long_entry():
    gan = _f("gàn", "tree trunk", "main part of sth", "to manage", "to work", "to do", "capable",
             "cadre", "to kill (slang)")
    r = _readings([gan])[0]["meanings"]
    assert len(r) == 6 and "to do" in r
