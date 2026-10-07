# -*- coding: utf-8 -*-
"""End-to-end tests of the viewer API against a throwaway base folder.
Each test replays one attack from the 2026-09 reviews (F01, F02, the
rebuttal's DNS-rebinding chain) or checks that normal use still works."""
import json

import pytest
from fastapi.testclient import TestClient

from conftest import BASE
from viewer import api, scanner
from viewer.config import PORT

ORIGIN = f"http://127.0.0.1:{PORT}"


@pytest.fixture
def client():
    c = TestClient(api.app, base_url=ORIGIN)
    r = c.get(f"/?t={api.TOKEN}", follow_redirects=False)
    assert r.status_code == 303 and api.COOKIE in r.cookies
    c.cookies.set(api.COOKIE, api.TOKEN)
    return c


def post(c, url, body, **headers):
    h = {"Content-Type": "application/json", "Origin": ORIGIN}
    h.update(headers)
    return c.post(url, content=json.dumps(body), headers={k: v for k, v in h.items() if v is not None})


# ---- DNS rebinding / session / CSRF ----

def test_rebinding_host_refused(client):
    r = client.get("/api/data", headers={"Host": "evil.example"})
    assert r.status_code == 421


def test_no_session_refused():
    c = TestClient(api.app, base_url=ORIGIN)
    assert c.get("/api/data").status_code == 401
    assert c.get("/raw?path=01_events/pic.png").status_code == 401
    assert c.get("/").status_code == 401
    assert c.get("/?t=wrong").status_code == 401


def test_cross_origin_post_refused(client):
    item = client.get("/api/item?path=01_events/2026-01-01_hello.md").json()
    r = post(client, "/api/item", {"path": item["path"], "raw": "x", "mtime": item["mtime"]},
             Origin="http://evil.example")
    assert r.status_code == 403


def test_non_json_post_refused(client):
    r = client.post("/api/quickadd", content="title=x",
                    headers={"Content-Type": "text/plain", "Origin": ORIGIN})
    assert r.status_code == 415


def test_security_headers(client):
    r = client.get("/api/data")
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert client.get("/openapi.json").status_code == 404


def test_data_does_not_expose_base_path(client):
    d = client.get("/api/data").json()
    assert "base" not in d and str(BASE) not in json.dumps(d)


# ---- path traversal (F02 + rebuttal) ----

@pytest.mark.parametrize("path", [
    "01_events/../99_system/PHILOSOPHY.md",
    "../base_evil/secret.md",
    "99_system/../../base_evil/secret.md",
])
def test_read_traversal_refused(client, path):
    assert client.get("/api/item", params={"path": path}).status_code == 400


def test_write_outside_editable_roots_refused(client):
    target = "01_events/../99_system/skills/x/SKILL.md"
    before = (BASE / "99_system/skills/x/SKILL.md").read_text(encoding="utf-8")
    r = post(client, "/api/item", {"path": target, "raw": "PWNED", "mtime": 0})
    assert r.status_code == 400
    r = post(client, "/api/item", {"path": "99_system/skills/x/SKILL.md", "raw": "PWNED", "mtime": 0})
    assert r.status_code == 400
    assert (BASE / "99_system/skills/x/SKILL.md").read_text(encoding="utf-8") == before


def test_kernel_docs_readable_not_editable(client):
    r = client.get("/api/item?path=99_system/PHILOSOPHY.md")
    assert r.status_code == 200 and r.json()["editable"] is False
    assert client.get("/api/item?path=INDEX.md").status_code == 200


# ---- stored XSS (F01) ----

def test_item_html_is_sanitised(client):
    html = client.get("/api/item?path=01_events/2026-01-01_hello.md").json()["html"]
    assert "<script" not in html and "<img" not in html
    assert "&lt;script&gt;" in html


def test_search_snippet_is_escaped(client):
    items = client.get("/api/search?q=needle").json()["items"]
    assert items, "fixture note should match"
    snip = items[0]["snippet"]
    assert "<script" not in snip and "<img" not in snip and "<mark>" in snip


# ---- /raw ----

@pytest.mark.parametrize("path,code", [
    (".git/config", 400), ("98_tools/data/index.db", 400), ("99_system/PHILOSOPHY.md", 400),
    ("01_events/page.html", 403), ("01_events/img.svg", 403),
])
def test_raw_refuses(client, path, code):
    assert client.get("/raw", params={"path": path}).status_code == code


def test_raw_serves_image(client):
    r = client.get("/raw?path=01_events/pic.png")
    assert r.status_code == 200 and r.headers["x-content-type-options"] == "nosniff"


# ---- live edit still works ----

def test_edit_roundtrip_and_mtime_guard(client):
    item = client.get("/api/item?path=01_events/2026-01-01_hello.md").json()
    new = item["raw"].replace("# Hello", "# Hello edited")
    r = post(client, "/api/item", {"path": item["path"], "raw": new, "mtime": item["mtime"]})
    assert r.status_code == 200
    assert "# Hello edited" in (BASE / item["path"]).read_text(encoding="utf-8")
    stale = post(client, "/api/item", {"path": item["path"], "raw": "x", "mtime": item["mtime"]})
    assert stale.status_code == 409


def test_edit_size_cap(client):
    item = client.get("/api/item?path=01_events/2026-01-01_hello.md").json()
    r = post(client, "/api/item", {"path": item["path"], "raw": "x" * 1_000_001, "mtime": item["mtime"]})
    assert r.status_code == 413


# ---- quick add ----

def test_quickadd_ok_and_no_injection(client):
    r = post(client, "/api/quickadd", {"title": "Hi\nvisibility: public", "text": "body",
                                        "circle": "work", "related": ["04_projects/p/index.md"]})
    assert r.status_code == 200
    raw = (BASE / r.json()["path"]).read_text(encoding="utf-8")
    meta, _ = scanner.parse_frontmatter(raw)
    assert "visibility" not in meta and meta["related"] == "04_projects/p/index.md"


def test_quickadd_related_injection_refused(client):
    r = post(client, "/api/quickadd", {"title": "x", "related": ["a\nvisibility: public"]})
    assert r.status_code == 400


def test_quickadd_same_minute_does_not_overwrite(client):
    a = post(client, "/api/quickadd", {"title": "Same", "text": "one"}).json()["path"]
    b = post(client, "/api/quickadd", {"title": "Same", "text": "two"}).json()["path"]
    assert a != b
    assert "one" in (BASE / a).read_text(encoding="utf-8")


# ---- frontmatter comments ----

def test_frontmatter_comment_stripped():
    meta, _ = scanner.parse_frontmatter(
        "---\nvisibility: public   # a comment\nlang: C#\nq: '# not a comment'\n---\nx")
    assert meta["visibility"] == "public" and meta["lang"] == "C#"
    assert meta["q"] == "# not a comment"


def test_a_list_in_a_scalar_field_does_not_break_the_index():
    """rc.3 review R6: `date: [2026-10-03]` made store.sync() fail for every note.
    A list is kept only where the field is a list (tags); elsewhere it is empty."""
    from viewer import scanner, store
    p = BASE / "01_events" / "2026-01-02_listdate.md"
    p.write_text("---\ntype: event\ncircle: work\ndate: [2026-01-02]\nstatus: [a, b]\nenergy: 4\n"
                 "tags: [x, 2]\nvisibility: private\n---\n# List date\n", encoding="utf-8")
    try:
        row = scanner.parse_file("01_events/2026-01-02_listdate.md", "event")
        assert row["date"] is None and row["status"] is None
        assert row["tags"] == "x,2" and row["energy"] == 4
        store.sync()                                                    # does not raise
    finally:
        p.unlink()
        store.sync()


def test_data_reports_the_trust_anchor_state(client, monkeypatch, tmp_path):
    """The viewer reads the anchor (never writes it): a steering file that changed
    since the owner anchored it is shown, not silently accepted (rc.4, D9)."""
    import json
    from aicowork_core import anchor as core_anchor
    monkeypatch.setenv("AICOWORK_ANCHOR_DIR", str(tmp_path / "anchors"))
    assert client.get("/api/data").json()["anchor"] == {"state": "none", "drifted": []}
    pol = BASE / "policy.yaml"
    pol.write_text("schema: 1\npreset: personal-simple\ndecided: 2026-10-01\ndistribution: private\n", encoding="utf-8")
    f = core_anchor.anchor_file(BASE)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"date": "2026-10-06", "steering": core_anchor.steering_hashes(BASE)}) + "\n", encoding="utf-8")
    assert client.get("/api/data").json()["anchor"] == {"state": "ok", "drifted": []}
    pol.write_text(pol.read_text(encoding="utf-8").replace("private", "controlled"), encoding="utf-8")
    assert client.get("/api/data").json()["anchor"] == {"state": "drift", "drifted": ["policy.yaml"]}
    pol.unlink()
