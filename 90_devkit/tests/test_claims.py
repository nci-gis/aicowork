# -*- coding: utf-8 -*-
"""Public claims (review of rc.2, finding 5): an absolute claim that nothing
leaves must name the model-call exception in the same passage."""
import json
from pathlib import Path

from devkit import claims

REPO = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir())


def _doc(tmp_path, text, name="README.md"):
    (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path


def test_the_repository_makes_no_unqualified_claim():
    assert claims.scan(REPO) == []


def test_the_rc2_sentence_is_caught(tmp_path):
    base = _doc(tmp_path, "## Steps\n\n1. Do this.\n\nNothing you do in these five steps can send anything anywhere.\n")
    assert [s for _, s in claims.scan(base)] == ["Nothing you do in these five steps can send anything anywhere."]


def test_a_claim_with_the_exception_nearby_passes(tmp_path):
    base = _doc(tmp_path, "Our tools send nothing anywhere; never sent, nothing leaves.\n\n"
                          "The assistant's provider sees what the assistant reads.\n")
    assert claims.scan(base) == []


def test_other_meanings_of_leave_are_not_claims(tmp_path):
    base = _doc(tmp_path, "The AI may set private or leave a value as is — never raise.\n\n"
                          "It leaves a tombstone receipt.\n")
    assert claims.scan(base) == []


def test_a_false_alarm_needs_the_owners_reason_and_date(tmp_path):
    s = "Nothing leaves this drawer."
    base = _doc(tmp_path, s + "\n")
    (tmp_path / "90_devkit").mkdir()
    f = tmp_path / claims.REVIEWED
    f.write_text(json.dumps({"false_alarms": [{"file": "README.md", "sentence": s}]}), encoding="utf-8")
    assert claims.scan(base)                                   # no reason, no date: still a claim
    f.write_text(json.dumps({"false_alarms": [{"file": "README.md", "sentence": s, "why": "a drawer, not data",
                                               "decided": "2026-10-03"}]}), encoding="utf-8")
    assert claims.scan(base) == []
