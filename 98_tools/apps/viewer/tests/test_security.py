# -*- coding: utf-8 -*-
"""Unit tests for viewer.security — the path, HTML and input rules."""
import os
import sys

import pytest

from conftest import BASE, SIBLING
from viewer import render, security
from viewer.security import PathRejected, safe_path

ROOTS = {"01_events", "00_inbox"}


@pytest.mark.parametrize("rel", [
    "01_events/../99_system/PHILOSOPHY.md",     # traversal past a root allow-list
    "../base_evil/secret.md",                   # sibling-prefix bypass
    "01_events/../../base_evil/secret.md",
    "/etc/passwd", "C:/Windows/win.ini", "c:secret.md",
    "//server/share/x.md", "\\\\?\\C:\\x.md",
    "01_events/a.md:stream", "01_events/a.md::$DATA",   # NTFS alternate data streams
    "01_events/CON", "01_events/nul.md", "01_events/com1.txt",  # device names
    "01_events/trailing. ", "01_events/dot.",
    "", "   ", ".", "01_events/..",
    "99_system/PHILOSOPHY.md",                  # root not in allow-list
    "INDEX.md",                                 # root file not allowed unless listed
])
def test_safe_path_rejects(rel):
    with pytest.raises(PathRejected):
        safe_path(BASE, rel, roots=ROOTS)


def test_safe_path_accepts_normal():
    p = safe_path(BASE, "01_events/2026-01-01_hello.md", roots=ROOTS)
    assert p == (BASE / "01_events" / "2026-01-01_hello.md").resolve()
    assert safe_path(BASE, "01_events\\2026-01-01_hello.md", roots=ROOTS) == p
    assert safe_path(BASE, "INDEX.md", roots=ROOTS, root_files=("INDEX.md",)).name == "INDEX.md"


def test_safe_path_rejects_symlink_or_junction():
    link = BASE / "01_events" / "linkdir"
    try:
        if sys.platform == "win32":
            import subprocess
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(SIBLING)],
                               capture_output=True)
            if r.returncode != 0:
                pytest.skip("cannot create a junction here")
        else:
            os.symlink(SIBLING, link)
    except OSError:
        pytest.skip("cannot create a link here")
    try:
        with pytest.raises(PathRejected):
            safe_path(BASE, "01_events/linkdir/secret.md", roots=ROOTS)
    finally:
        os.rmdir(link) if sys.platform == "win32" else os.unlink(link)


@pytest.mark.parametrize("src,bad", [
    ("<img src=x onerror=alert(1)>", "<img"),
    ("<script>alert(1)</script>", "<script"),
    ("<div onclick='x'>a</div>", "<div"),
    ("[x](javascript:alert(1))", 'href="javascript'),
    ("[x]( JaVaScRiPt:alert(1))", 'href="javascript'),
    ("[x](data:text/html,hi)", 'href="data:'),
    ("[x](vbscript:msgbox)", 'href="vbscript'),
    ("![p](https://evil.example/t.png)", "<img"),   # remote image -> link, not a fetch
])
def test_markdown_neutralises(src, bad):
    html = render.make_markdown().convert(src).lower()
    assert bad not in html


def test_markdown_keeps_normal_content():
    html = render.make_markdown().convert(
        "# T\n\n[a](https://x.y) [b](../01_events/a.md) [c](mailto:a@b.c)\n\n![l](img.png)\n\n| a |\n|---|\n| 1 |")
    for s in ('href="https://x.y"', 'href="../01_events/a.md"', 'href="mailto:a@b.c"',
              '<img alt="l" src="img.png"', "<table>"):
        assert s in html


def test_markdown_escapes_raw_html():
    html = render.make_markdown().convert("<img src=x onerror=alert(1)> & <b>x</b>")
    assert "<img" not in html and "<b>" not in html
    assert "&lt;img" in html and "&amp;" in html


def test_snippet_escaped_but_marks_kept():
    raw = f"a <script>x</script> {security.SNIP_OPEN}needle{security.SNIP_CLOSE} b"
    out = security.safe_snippet(raw)
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "<mark>needle</mark>" in out


def test_related_rejects_injection():
    for bad in (["x\nvisibility: public"], ["../x.md"], ["/abs"], ["a]"], ["a,b"],
                ["a:b"], ["x"] * 6):
        with pytest.raises(PathRejected):
            security.clean_related(bad)
    assert security.clean_related(["04_projects/a b/index.md"]) == ["04_projects/a b/index.md"]


def test_title_control_chars_stripped():
    assert security.clean_title("a\nvisibility: public\r\x00b") == "a visibility: public  b"
    assert len(security.clean_title("x" * 999)) == 200


def test_atomic_write_keeps_old_file_on_failure(tmp_path, monkeypatch):
    f = tmp_path / "a.md"
    f.write_text("old", encoding="utf-8")

    def boom(*a, **k):
        raise OSError("disk full")
    from aicowork_core import fsafe                       # shared with the CLI
    monkeypatch.setattr(fsafe.os, "replace", boom)
    with pytest.raises(OSError):
        security.atomic_write(f, "new")
    assert f.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.iterdir()) == [f]            # no temp file left behind


def test_exclusive_create_never_overwrites(tmp_path):
    f = tmp_path / "n.md"
    security.exclusive_create(f, "one")
    with pytest.raises(FileExistsError):
        security.exclusive_create(f, "two")
    assert f.read_text(encoding="utf-8") == "one"


def test_origin_and_hosts():
    assert "127.0.0.1:8765" in security.allowed_hosts(8765)
    assert "evil.example:8765" not in security.allowed_hosts(8765)
    assert security.origin_ok(None, "127.0.0.1:8765")
    assert security.origin_ok("http://127.0.0.1:8765", "127.0.0.1:8765")
    assert not security.origin_ok("http://evil.example", "127.0.0.1:8765")
