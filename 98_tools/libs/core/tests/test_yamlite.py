# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from aicowork_core.yamlite import YamlError, loads, load

KERNEL = next(p for p in Path(__file__).resolve().parents if (p / "99_system").is_dir()) / "99_system"


def test_example_config_and_presets_parse():
    cfg = load(KERNEL / "aicowork.example.yaml")
    assert cfg["language"]["chat"] == ["en"]
    assert cfg["language"]["modules"] == {"99_system": "en", "templates": "en"}
    assert cfg["apps"][0] == {"id": "dashboard", "name": "Dashboard (Today + Launcher)",
                              "kind": "route", "target": "/", "circle": "all"}
    assert cfg["server"] == {"host": "127.0.0.1", "port": 8765}
    assert cfg["modules"] == ["7habits"]
    for p in (KERNEL / "presets").glob("*.yaml"):
        pol = load(p)
        assert pol["schema"] == 1 and "ai_surfaces" in pol
    mod = load(KERNEL / "modules" / "7habits" / "module.yaml")
    assert mod["provides"]["fields"] == ["q", "role"]
    assert mod["permissions"]["write"] == ["06_logs/**"]


def test_scalars_and_flow():
    d = loads("a: 1\nb: true\nc: ~\nd: 'x # y'\ne: \"q\"\nf: plain text # c\n"
              "g: [1, 'two', [3]]\nh: {x: 1, y: [a, b]}\ni: 0.0.1\nj:\n")
    assert d == {"a": 1, "b": True, "c": None, "d": "x # y", "e": "q", "f": "plain text",
                 "g": [1, "two", [3]], "h": {"x": 1, "y": ["a", "b"]}, "i": "0.0.1", "j": None}


def test_nested_lists_and_maps():
    d = loads("top:\n  - a\n  - b\nlist_at_same_indent:\n- x\n- y\nm:\n  k:\n    deep: 1\n"
              "items:\n  - id: 1\n    name: one\n  - id: 2\n")
    assert d["top"] == ["a", "b"]
    assert d["list_at_same_indent"] == ["x", "y"]
    assert d["m"] == {"k": {"deep": 1}}
    assert d["items"] == [{"id": 1, "name": "one"}, {"id": 2}]


@pytest.mark.parametrize("text,line", [
    ("a: 1\n\tb: 2\n", 2),
    ("a: &anchor 1\n", 1),
    ("a: *alias\n", 1),
    ("a: !!str 1\n", 1),
    ("a: |\n  multi\n", 1),
    ("a: 1\n---\nb: 2\n", 2),
    ("a: 1\na: 2\n", 2),
    ("a: [1, 2\n", 1),
    ("just a sentence\n", 1),
    ("a: 1\n    b: 2\n", 2),
    ("a: 'open\n", 1),
])
def test_rejects_outside_subset(text, line):
    with pytest.raises(YamlError) as e:
        loads(text)
    assert e.value.line == line


def test_empty():
    assert loads("") == {} and loads("# only a comment\n") == {}
