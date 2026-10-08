# -*- coding: utf-8 -*-
"""Triage plans in the viewer (rc.6, E7): the agent writes 06_logs/triage/<date>_<n>_plan.json
and stops; the owner applies or dismisses from the Inbox card. One code path with
`aicowork triage --apply` (aicowork_core.triage_plan)."""
import json

import pytest
from fastapi.testclient import TestClient

from conftest import BASE
from viewer import api
from viewer.config import PORT

ORIGIN = f"http://127.0.0.1:{PORT}"
PLANS = BASE / "06_logs" / "triage"


@pytest.fixture
def client():
    c = TestClient(api.app, base_url=ORIGIN)
    c.get(f"/?t={api.TOKEN}", follow_redirects=False)
    c.cookies.set(api.COOKIE, api.TOKEN)
    return c


def post(c, url, body):
    return c.post(url, json=body, headers={"Origin": ORIGIN, "Content-Type": "application/json"})


def _plan(name, moves):
    PLANS.mkdir(parents=True, exist_ok=True)
    (PLANS / name).write_text(json.dumps({"moves": moves}), encoding="utf-8")


@pytest.fixture
def inbox_items():
    a = BASE / "00_inbox" / "mail-from-sender.md"
    a.write_text("---\ntype: note\nvisibility: public\ncircle: work\ndate: 2026-02-01\n---\n# A sender's note\n", encoding="utf-8")
    b = BASE / "00_inbox" / "clip.txt"
    b.write_text("a clipping\n", encoding="utf-8")
    yield a, b
    for p in (a, b):
        if p.exists():
            p.unlink()
    for p in list(PLANS.glob("*")) if PLANS.is_dir() else []:
        p.unlink()
    for p in (BASE / "02_emails").glob("2026-02-01_*"):
        p.unlink()
    for p in (BASE / "07_archive").glob("clip*"):
        p.unlink()


def test_pending_plans_are_listed_checked_and_applied_by_the_owner(client, inbox_items):
    _plan("2026-02-02_1_plan.json", [
        {"from": "00_inbox/mail-from-sender.md", "to": "02_emails/2026-02-01_senders-note.md", "type": "email", "circle": "work"},
        {"from": "00_inbox/clip.txt", "to": "07_archive/clip.txt", "note": "stale"}])
    _plan("2026-02-02_2_plan.json", [{"from": "00_inbox/clip.txt", "to": "../outside.txt"}])
    d = client.get("/api/data").json()
    plans = {p["name"]: p for p in d["triage_plans"]}
    assert set(plans) == {"2026-02-02_1_plan.json", "2026-02-02_2_plan.json"}
    assert plans["2026-02-02_1_plan.json"]["error"] is None and len(plans["2026-02-02_1_plan.json"]["moves"]) == 2
    assert plans["2026-02-02_2_plan.json"]["error"]                     # a plan outside the rules: shown, not runnable
    # apply: the same rules — the sender's `visibility: public` becomes private
    r = post(client, "/api/triage/apply", {"name": "2026-02-02_1_plan.json"})
    assert r.status_code == 200, r.text
    assert r.json()["moves"] == 2 and r.json()["report"].startswith("06_logs/audit/")
    moved = BASE / "02_emails" / "2026-02-01_senders-note.md"
    assert moved.is_file() and "visibility: private" in moved.read_text(encoding="utf-8")
    assert not (PLANS / "2026-02-02_1_plan.json").exists() and (PLANS / "2026-02-02_1_applied.json").is_file()
    # the bad plan cannot be applied; it can be dismissed and stays as a record
    assert post(client, "/api/triage/apply", {"name": "2026-02-02_2_plan.json"}).status_code == 400
    r = post(client, "/api/triage/apply", {"name": "2026-02-02_2_plan.json", "action": "dismiss"})
    assert r.status_code == 200 and (PLANS / "2026-02-02_2_dismissed.json").is_file()
    assert client.get("/api/triage/plans").json()["plans"] == []


def test_plan_names_are_validated(client, inbox_items):
    for bad in ("../policy.yaml", "x_plan.json/../../INDEX.md", "notes.md", "2026-02-02_1_applied.json", ""):
        assert post(client, "/api/triage/apply", {"name": bad}).status_code == 400, bad
    assert post(client, "/api/triage/apply", {"name": "2026-02-02_9_plan.json"}).status_code == 400   # no such plan
    assert post(client, "/api/triage/apply", {"name": "2026-02-02_1_plan.json", "action": "delete"}).status_code == 400
