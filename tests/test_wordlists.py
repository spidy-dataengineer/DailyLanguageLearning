"""Tests for the local word lists, Tatoeba sentences and CC-CEDICT in content/data."""
import gzip

from content import dedup, sources


def _data(tmp_path, monkeypatch):
    (tmp_path / "wordlist_en.tsv").write_text(
        "TSL\tinvoice\tinvoice,invoices\nTSL\tart\tart,arts\nNAWL\tmitigate\tmitigate,mitigated\n", encoding="utf-8")
    (tmp_path / "tatoeba_eng.tsv").write_text(
        "1\tPlease send the invoices today.\n2\tWe start the meeting now.\n3\tI love modern art very much.\n", encoding="utf-8")
    (tmp_path / "tatoeba_cmn.tsv").write_text("7\t我爱你。\n8\t他在家。\n", encoding="utf-8")
    with gzip.open(tmp_path / "cedict.txt.gz", "wt", encoding="utf-8") as f:
        f.write("# comment\n北京 北京 [Bei3 jing1] /Beijing/capital/\n")
    monkeypatch.setattr(sources, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(sources, "_tatoeba_cache", {})
    monkeypatch.setattr(sources, "_cedict_cache", {})


def test_wordlist_candidates_skip_saved_words_in_any_form(tmp_path, monkeypatch):
    _data(tmp_path, monkeypatch)
    assert [c["word"] for c in dedup.wordlist_candidates([{"expression": "Invoices"}], "TSL")] == ["art"]
    assert dedup.wordlist_candidates([{"expression": "to mitigate"}], "NAWL") == []


def test_sentences_match_whole_words_and_carry_the_credit_link(tmp_path, monkeypatch):
    _data(tmp_path, monkeypatch)
    [art] = dedup.wordlist_candidates([{"expression": "invoice"}], "TSL")
    assert art["tatoeba"] == [{"text": "I love modern art very much.", "url": "https://tatoeba.org/en/sentences/show/3"}]


def test_chinese_samples_filter_by_word(tmp_path, monkeypatch):
    _data(tmp_path, monkeypatch)
    assert [r["text"] for r in sources.tatoeba_samples("cmn", contains=["爱"])] == ["我爱你。"]


def test_missing_files_give_nothing_instead_of_failing(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "DATA_DIR", str(tmp_path / "none"))
    monkeypatch.setattr(sources, "_tatoeba_cache", {})
    monkeypatch.setattr(sources, "_cedict_cache", {})
    assert sources.english_wordlist("TSL") == []
    assert sources.tatoeba_samples("eng") == []
    assert sources.cedict_readings("北京") == []


def test_cedict_readings(tmp_path, monkeypatch):
    _data(tmp_path, monkeypatch)
    assert sources.cedict_readings("北京") == [{"pinyin": "Bei3 jing1", "meanings": ["Beijing", "capital"]}]
    assert sources.cedict_readings("없는말") == []
