"""Build content/data/ from the downloaded word lists and dictionaries. Run by hand to refresh them:

    python content/prepare_sources.py <download_dir>

The folder needs eng_sentences.tsv.bz2 and cmn_sentences.tsv.bz2 (tatoeba.org/en/downloads),
cedict_1_0_ts_utf-8_mdbg.txt.gz (mdbg.net) and {TSL,NAWL}_12_lemmatized_for_teaching.csv (newgeneralservicelist.com).
Licences and attribution: content/data/README.md.
"""
import bz2
import os
import re
import shutil
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EN_WORDS = (5, 15)  # sentence length a card can use
ZH_MAX_CHARS = 30
PER_WORD = 8  # English sentences kept per list word; all 2 million would not fit in the repo


def lemma_rows(path):
    """Each non-comment line is the headword and its inflected forms."""
    with open(path, encoding="latin-1") as f:
        for line in f:
            forms = [w.strip().lower() for w in line.split(",") if w.strip()]
            if forms and not forms[0].startswith("#"):
                yield forms


def main(src):
    os.makedirs(OUT, exist_ok=True)
    wanted = {}  # inflected form -> headwords wanting a sentence with it
    with open(os.path.join(OUT, "wordlist_en.tsv"), "w", encoding="utf-8", newline="\n") as out:
        for name in ("TSL", "NAWL"):
            for forms in lemma_rows(os.path.join(src, f"{name}_12_lemmatized_for_teaching.csv")):
                out.write(f"{name}\t{forms[0]}\t{','.join(forms)}\n")
                for form in forms:
                    wanted.setdefault(form, set()).add(forms[0])

    kept = {}
    with bz2.open(os.path.join(src, "eng_sentences.tsv.bz2"), "rt", encoding="utf-8") as f, \
            open(os.path.join(OUT, "tatoeba_eng.tsv"), "w", encoding="utf-8", newline="\n") as out:
        for line in f:
            sid, _, text = line.rstrip("\n").split("\t", 2)
            if not EN_WORDS[0] <= len(text.split()) <= EN_WORDS[1]:
                continue
            heads = {h for w in re.findall(r"[a-z']+", text.lower()) for h in wanted.get(w, ())}
            heads = [h for h in heads if kept.get(h, 0) < PER_WORD]
            if heads:
                for h in heads:
                    kept[h] = kept.get(h, 0) + 1
                out.write(f"{sid}\t{text}\n")

    with bz2.open(os.path.join(src, "cmn_sentences.tsv.bz2"), "rt", encoding="utf-8") as f, \
            open(os.path.join(OUT, "tatoeba_cmn.tsv"), "w", encoding="utf-8", newline="\n") as out:
        for line in f:
            sid, _, text = line.rstrip("\n").split("\t", 2)
            if len(text) <= ZH_MAX_CHARS:
                out.write(f"{sid}\t{text}\n")

    shutil.copy(os.path.join(src, "cedict_1_0_ts_utf-8_mdbg.txt.gz"), os.path.join(OUT, "cedict.txt.gz"))


if __name__ == "__main__":
    main(sys.argv[1])
