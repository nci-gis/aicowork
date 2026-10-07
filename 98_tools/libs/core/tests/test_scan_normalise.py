# -*- coding: utf-8 -*-
"""The leak gate's normalisation (CONVENTIONS "Session rules" 5, L2-LEAK-NORM) and
the hidden-character report (L2-HIDDEN)."""
from pathlib import Path

import pytest

from aicowork_core import common as C
from aicowork_core.scan import hidden_chars, normalise, variants

KERNEL = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir()) / "99_system"
LEAK = KERNEL / "conformance" / "fixtures" / "leak"
TOKENS = {"Minh Tran", "MinhTran"}       # the example instance's check_tokens


def hit(text, tokens=TOKENS):
    pats = C.token_patterns(tokens)
    for layer, v in variants(text):
        for tok, rx in pats:
            if rx.search(v):
                return layer or "plain"
    return None


@pytest.mark.parametrize("name,layer", [
    ("01_confusable.md", "look-alike or invisible characters"),
    ("02_zero-width.md", "look-alike or invisible characters"),
    ("03_soft-break.md", "a soft line break"),
    ("04_percent.md", "percent encoding"),
    ("05_entity.md", "HTML entities"),
    ("06_base64.md", "base64"),
])
def test_every_leak_fixture_is_caught(name, layer):
    assert hit((LEAK / name).read_text(encoding="utf-8")) == layer


def test_plain_text_hits_plainly_and_clean_text_does_not():
    assert hit("Agreed with Minh Tran.") == "plain"
    assert hit("Agreed with Minh Tuan and the forecast.") is None
    assert hit("Transport: tram and train.") is None          # no false positive on Tran/Minh parts


def test_normalise_maps_lookalikes_and_drops_invisibles():
    assert normalise("Mіnh Trаn") == "Minh Tran"
    assert normalise("ﬁle") == "file"                        # NFKC ligature
    assert variants("Mi​nh­ Tran")[1][1] == "Minh Tran"


def test_hidden_chars_reports_what_a_person_cannot_see():
    out = hidden_chars("ok line\nhid​den\nMіnh\n‮right-to-left\nfamily 👨‍👩‍👧 fine")
    kinds = [(n, k) for n, k, _ in out]
    assert (2, "invisible character") in kinds
    assert (3, "mixed scripts") in kinds
    assert (4, "invisible character") in kinds
    assert not [x for x in out if x[0] == 5]                     # the emoji ZWJ sequence is not reported
    assert hidden_chars("Tiếng Việt có dấu, không sao cả.") == []
    assert hidden_chars("Ελληνικά alone is one script") == []
