# -*- coding: utf-8 -*-
"""Ambiguity: the kernel's classes (conformance/ambiguity.json), their fixtures,
and the reference detector. A note that can be read two ways is read the
fail-closed way and reported; a note that reads one way is left alone."""
import json
from pathlib import Path

import pytest

from aicowork_core import ambiguity as A
from aicowork_core import common as C
from aicowork_core.frontmatter import parse_frontmatter, parse_frontmatter_strict

KERNEL = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir()) / "99_system"
REGISTRY = json.loads((KERNEL / "conformance" / "ambiguity.json").read_text(encoding="utf-8"))
CLASSES = {c["id"]: c for c in REGISTRY["classes"]}
OPEN, CLOSE = A.PRIVATE_OPEN, A.PRIVATE_CLOSE


def classes_of(text):
    return {p.cls for p in A.problems(text)}


# ---------------- the registry and its fixtures ----------------

def test_every_class_is_complete():
    for c in REGISTRY["classes"]:
        for key in ("id", "surface", "kind", "looks_like", "read_as", "fix", "fixture"):
            assert c.get(key), (c.get("id"), key)
        assert c["kind"] in ("grammar", "lookalike")


@pytest.mark.parametrize("cid", sorted(CLASSES))
def test_each_fixture_matches_its_class_and_no_other(cid):
    text = (KERNEL / "conformance" / CLASSES[cid]["fixture"]).read_text(encoding="utf-8")
    assert classes_of(text) == {cid}


def test_clean_fixture_matches_nothing():
    text = (KERNEL / "conformance" / "fixtures" / "ambiguity" / "clean.md").read_text(encoding="utf-8")
    assert A.problems(text) == []


def test_the_example_instance_reads_one_way():
    example = KERNEL / "conformance" / "fixtures" / "example-instance"
    found = {p.relative_to(example).as_posix(): A.problems(p.read_text(encoding="utf-8"))
             for p in example.rglob("*.md") if p.parts[-2] != "00_inbox"}
    assert {k: v for k, v in found.items() if v} == {}


# ---------------- frontmatter ----------------

NOTE = "---\ntype: note\ncircle: work\n{}\n---\n# Body\n"


@pytest.mark.parametrize("fm, cls", [
    ('visibility: "public', "AMB-FM-SYNTAX"),                        # review finding 1: unclosed quote
    ("visibility: private\nmetadata:\n  visibility: public", "AMB-FM-VIS-KEY"),   # review finding 1: nested
    ("visibility: private\nvisibility: public", "AMB-FM-SYNTAX"),    # a key written twice
    ("Visibility: public", "AMB-FM-VIS-KEY"),
    ("visiblity: public", "AMB-FM-VIS-KEY"),
    ("visibility: public\nmeta:\n  visibility: private", "AMB-FM-VIS-KEY"),
    ("visibility: Public", "AMB-FM-VIS-VALUE"),
    ("visibility: [public]", "AMB-FM-VIS-VALUE"),
    ("visibility: public\n\tdate: 2026-10-03", "AMB-FM-SYNTAX"),     # tab in the indentation
    ("visibility: public\ndate: {{YYYY-MM-DD}}", "AMB-FM-SYNTAX"),   # placeholder left unfilled
])
def test_frontmatter_ambiguity_reads_private(fm, cls):
    text = NOTE.format(fm)
    meta, _, problems = parse_frontmatter_strict(text)
    assert cls in {p.cls for p in problems}
    assert C.visibility(meta) == "private"


@pytest.mark.parametrize("text", [
    "﻿" + NOTE.format("visibility: public"),                    # a byte-order mark before the fence
    "\n" + NOTE.format("visibility: public"),                        # a blank line before the fence
    "---\ntype: note\nvisibility: public\n--\n# the fence is one dash short\n",
    "---\ntype: note\nvisibility: public\n# never closed\n",
])
def test_a_fence_that_only_looks_right_reads_private(text):
    meta, _, problems = parse_frontmatter_strict(text)
    assert [p.cls for p in problems] == ["AMB-FM-FENCE"]
    assert C.visibility(meta) == "private"


def test_what_the_grammar_allows_reads_one_way():
    text = ("---\r\ntype: note\r\nvisibility: public   # a comment\r\nlang: C#\r\nq: '# not a comment'\r\n"
            "tags: [a, b]\r\nmeta:\r\n  reviewed: true\r\nenergy:\r\n---  \r\n# Body\r\n")
    meta, body, problems = parse_frontmatter_strict(text)
    assert problems == []
    assert meta["visibility"] == "public" and meta["lang"] == "C#" and meta["q"] == "# not a comment"
    assert meta["tags"] == ["a", "b"] and meta["energy"] == "" and meta["meta"] == {"reviewed": True}
    assert "# Body" in body


def test_no_frontmatter_is_not_an_ambiguity():
    assert parse_frontmatter("# Just a body\n---\nwith a rule\n") == ({}, "# Just a body\n---\nwith a rule\n")
    assert A.problems("# Just a body\n") == []


# ---------------- private blocks ----------------

@pytest.mark.parametrize("body, cls", [
    (f"{OPEN}outer\n{OPEN}inner{CLOSE}\ntail{CLOSE}", "AMB-PB-NEST"),     # review finding 2
    (f"{CLOSE}shared{OPEN}SECRET", "AMB-PB-ORPHAN"),                      # equal counts, wrong order
    (f"{OPEN}a{CLOSE}{CLOSE}shared{OPEN}SECRET", "AMB-PB-ORPHAN"),
    (f"{OPEN}never closed", "AMB-PB-ORPHAN"),
    ("<!--🔒 private-->SECRET<!-- /🔒 -->", "AMB-PB-NEAR"),
    ("<!-- 🔒 Private -->SECRET", "AMB-PB-NEAR"),
    ("<!-- private -->SECRET<!-- /private -->", "AMB-PB-NEAR"),
    ("<!-- 🔐 private -->SECRET", "AMB-PB-NEAR"),
    ("<!-- 🔒 private --SECRET", "AMB-PB-NEAR"),                         # rc.3 review R4: marker lost its `>`
    ("<!-- 🔒 private ->SECRET" + CLOSE, "AMB-PB-NEAR"),
    ("<!-- private\nSECRET", "AMB-PB-NEAR"),                              # unclosed, word form
])
def test_private_block_ambiguity_refuses(body, cls):
    assert cls in classes_of(NOTE.format("visibility: public") + body)
    with pytest.raises(ValueError):
        A.private_spans(body)


def test_private_blocks_found_exactly():
    body = f"a{OPEN}one{CLOSE}b\n{OPEN}\ntwo\n{CLOSE}c <!-- an ordinary comment --> {A.PLACEHOLDER}"
    assert A.private_block_problems(body) == []
    assert [body[s:e] for s, e in A.private_spans(body)] == [f"{OPEN}one{CLOSE}", f"{OPEN}\ntwo\n{CLOSE}"]


# ---------------- the owner file: the deny-list is read exactly or not at all ----------------

def _me(tmp_path, fm):
    (tmp_path / "03_personas").mkdir(exist_ok=True)
    (tmp_path / "03_personas" / "me.md").write_text(f"---\ntype: persona\ncircle: work\n{fm}\n---\n# Me\n", encoding="utf-8")
    return tmp_path


def test_check_tokens_read_exactly(tmp_path):
    assert C.check_tokens(_me(tmp_path, "check_tokens: [Alpha Co, 'Beta']   # names")) == {"Alpha Co", "Beta"}
    assert C.check_tokens(_me(tmp_path, "check_tokens: []")) == set()


@pytest.mark.parametrize("fm", [
    "check_tokens:\n  - Alpha Co",           # a block list: the old reader saw an empty list
    "check_tokens: Alpha Co",                # one name, not a list
    "check_tokens: [Alpha Co]\ndate: {{YYYY-MM-DD}}",
    "check_tokens: [Alpha Co]\ncheck_tokens: [Beta]",
])
def test_check_tokens_fail_closed_when_unclear(tmp_path, fm):
    base = _me(tmp_path, fm)
    if fm.startswith("check_tokens:\n"):
        assert C.check_tokens(base) == {"Alpha Co"}            # a block list is valid YAML: read exactly
        return
    assert C.check_tokens(base) is None and C.owner_file_problem(base)
    assert C.deny_list(base)[0] is None                        # every leak gate refuses


@pytest.mark.parametrize("text", [
    "# Me\nName: Alpha Co\n",                                   # rc.3 review R3a: no frontmatter
    "---\n---\n# Me\n",                                          # an empty one
])
def test_owner_file_without_frontmatter_refuses(tmp_path, text):
    (tmp_path / "03_personas").mkdir()
    (tmp_path / "03_personas" / "me.md").write_text(text, encoding="utf-8")
    assert C.owner_file_problem(tmp_path) and C.check_tokens(tmp_path) is None
    assert C.deny_list(tmp_path)[0] is None


@pytest.mark.parametrize("fm, tokens", [
    ('check_tokens: ["Synth\\x65tic Co"]', {"Synthetic Co"}),     # rc.3 review R3b: escapes decoded
    ('check_tokens: ["Alpha\\u0020Co", Beta]', {"Alpha Co", "Beta"}),
    ("check_tokens: ['O''Brien Co']", {"O'Brien Co"}),             # YAML's escaped single quote
    ('check_tokens: ["a \\"quoted\\" Co, Ltd"]  # c', {'a "quoted" Co, Ltd'}),
])
def test_check_tokens_quoted_values_read_exactly(tmp_path, fm, tokens):
    assert C.check_tokens(_me(tmp_path, fm)) == tokens


@pytest.mark.parametrize("fm", ['check_tokens: ["bad \\q escape"]', 'check_tokens: ["x\\u12"]', 'check_tokens: ["x" y]'])
def test_check_tokens_unclear_escape_refuses(tmp_path, fm):
    base = _me(tmp_path, fm)
    assert C.check_tokens(base) is None and C.owner_file_problem(base)
