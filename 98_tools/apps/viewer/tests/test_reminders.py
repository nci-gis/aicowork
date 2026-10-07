# -*- coding: utf-8 -*-
"""Reminders in the viewer: "Keep an eye" lists them with their computed state,
Done writes `last_done` and nothing else, and the cache is only a cache."""
import datetime as dt
import json

import pytest
from fastapi.testclient import TestClient

from conftest import BASE
from viewer import api, store
from viewer.config import DB_PATH, PORT

ORIGIN = f"http://127.0.0.1:{PORT}"
TODAY = dt.date.today()
FOLDER = BASE / "10_reminders"


def reminder(start, days, last_done="", repeat="monthly", eol="\n"):
    lines = ["---", "type: reminder", "visibility: private", "circle: work", f"date: {start}",
             "until:", f"repeat: {repeat}", f"days: {days}", f"last_done: {last_done}".rstrip(),
             "status: active   # active | paused | done", "---", "# Check the account", ""]
    return eol.join(lines)


@pytest.fixture
def client():
    c = TestClient(api.app, base_url=ORIGIN)
    c.get(f"/?t={api.TOKEN}", follow_redirects=False)
    c.cookies.set(api.COOKIE, api.TOKEN)
    return c


@pytest.fixture
def reminders():
    """upcoming (in 3 days), due (today), overdue (window ended 4 days ago)."""
    FOLDER.mkdir(exist_ok=True)
    start = (TODAY - dt.timedelta(days=60)).isoformat()
    up, due, over = (TODAY + dt.timedelta(days=3)), TODAY, (TODAY - dt.timedelta(days=4))
    files = {
        # weekly rules keep every case inside one period whatever today is
        "up.md": reminder(start, f"[{up.strftime('%a').lower()}]", (up - dt.timedelta(days=1)).isoformat(), "weekly"),
        "due.md": reminder(start, f"[{due.strftime('%a').lower()}]", (due - dt.timedelta(days=1)).isoformat(), "weekly"),
        "over.md": reminder(start, f"[{over.strftime('%a').lower()}]", (over - dt.timedelta(days=1)).isoformat(), "weekly"),
    }
    for name, text in files.items():
        (FOLDER / name).write_text(text, encoding="utf-8", newline="")
    yield files
    for name in list(files) + ["crlf.md"]:
        (FOLDER / name).unlink(missing_ok=True)


def post(c, url, body):
    return c.post(url, content=json.dumps(body),
                  headers={"Content-Type": "application/json", "Origin": ORIGIN})


def keep_an_eye(c):
    d = c.get("/api/data").json()
    return {e["path"]: e for e in d["upcoming"] if e["kind"] == "reminder"}, d


def test_data_lists_upcoming_due_and_overdue(client, reminders):
    rows, d = keep_an_eye(client)
    assert rows["10_reminders/up.md"]["state"] == "upcoming" and rows["10_reminders/up.md"]["days_left"] == 3
    assert rows["10_reminders/due.md"]["state"] == "due" and rows["10_reminders/due.md"]["days_left"] == 0
    over = rows["10_reminders/over.md"]
    assert over["state"] == "overdue" and over["days_left"] == -4 and over["missed"] == 1
    order = [e["path"] for e in d["upcoming"] if e["kind"] == "reminder"]
    assert order.index("10_reminders/over.md") < order.index("10_reminders/due.md") < order.index("10_reminders/up.md")
    assert d["counts"]["reminder"] == 3
    assert "reminder" not in d["balance"]["work"]          # duties are not presence (#8)


def test_done_writes_only_last_done(client, reminders):
    p = FOLDER / "over.md"
    before = p.read_text(encoding="utf-8")
    item = client.get("/api/item?path=10_reminders/over.md").json()
    r = post(client, "/api/reminder/done", {"path": "10_reminders/over.md", "mtime": item["mtime"]})
    assert r.status_code == 200, r.text
    after = p.read_text(encoding="utf-8")
    changed = [(a, b) for a, b in zip(before.splitlines(), after.splitlines()) if a != b]
    assert changed == [(next(l for l in before.splitlines() if l.startswith("last_done:")),
                        f"last_done: {TODAY.isoformat()}")]
    assert "status: active   # active | paused | done" in after
    rows, _ = keep_an_eye(client)
    assert "10_reminders/over.md" not in rows or rows["10_reminders/over.md"]["state"] == "upcoming"


def test_done_keeps_crlf(client, reminders):
    p = FOLDER / "crlf.md"
    p.write_bytes(reminder("2026-01-01", "[1]", eol="\r\n").encode("utf-8"))
    item = client.get("/api/item?path=10_reminders/crlf.md").json()
    assert post(client, "/api/reminder/done", {"path": "10_reminders/crlf.md", "mtime": item["mtime"]}).status_code == 200
    raw = p.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
    assert f"last_done: {TODAY.isoformat()}\r\n".encode() in raw


def test_done_refuses_stale_outside_and_bad_dates(client, reminders):
    item = client.get("/api/item?path=10_reminders/due.md").json()
    path = "10_reminders/due.md"
    assert post(client, "/api/reminder/done", {"path": path, "mtime": item["mtime"] - 5}).status_code == 409
    future = (TODAY + dt.timedelta(days=1)).isoformat()
    assert post(client, "/api/reminder/done", {"path": path, "mtime": item["mtime"], "date": future}).status_code == 400
    early = (TODAY - dt.timedelta(days=365)).isoformat()      # before `date:`
    assert post(client, "/api/reminder/done", {"path": path, "mtime": item["mtime"], "date": early}).status_code == 400
    assert post(client, "/api/reminder/done", {"path": path, "mtime": item["mtime"], "date": "15/10"}).status_code == 400
    ev = client.get("/api/item?path=01_events/2026-01-01_hello.md").json()
    assert post(client, "/api/reminder/done", {"path": "01_events/2026-01-01_hello.md", "mtime": ev["mtime"]}).status_code == 400
    assert post(client, "/api/reminder/done", {"path": "10_reminders/../01_events/2026-01-01_hello.md",
                                               "mtime": ev["mtime"]}).status_code == 400
    # an explicit past date inside the range is accepted
    yday = (TODAY - dt.timedelta(days=1)).isoformat()
    r = post(client, "/api/reminder/done", {"path": path, "mtime": item["mtime"], "date": yday})
    assert r.status_code == 200 and r.json()["last_done"] == yday


def test_rebuilt_cache_gives_the_same_answer(client, reminders):
    before, _ = keep_an_eye(client)
    with store._lock:
        if store._db is not None:
            store._db.close()
            store._db = None
        DB_PATH.unlink()
    after, _ = keep_an_eye(client)
    assert after == before and len(after) == 3


def test_paused_and_invalid_reminders_are_not_shown(client, reminders):
    p = FOLDER / "due.md"
    p.write_text(reminders["due.md"].replace("status: active", "status: paused"), encoding="utf-8")
    rows, _ = keep_an_eye(client)
    assert "10_reminders/due.md" not in rows
    p.write_text(reminders["due.md"].replace("days: [", "days: [zz, "), encoding="utf-8")
    rows, _ = keep_an_eye(client)
    assert "10_reminders/due.md" not in rows


def test_only_valid_type_reminder_files_are_computed(client, reminders):
    p = FOLDER / "due.md"
    # `days: 15, 16` without brackets is one string, invalid for conformance — not computed here either
    p.write_text(reminders["due.md"].replace("repeat: weekly", "repeat: monthly").split("days:")[0]
                 + "days: 15, 16\nlast_done:\nstatus: active\n---\n# x\n", encoding="utf-8")
    rows, _ = keep_an_eye(client)
    assert "10_reminders/due.md" not in rows
    p.write_text(reminders["due.md"].replace("type: reminder\n", ""), encoding="utf-8")
    rows, _ = keep_an_eye(client)
    assert "10_reminders/due.md" not in rows


def test_dashboard_rows_carry_the_mtime_done_checks(client, reminders):
    rows, _ = keep_an_eye(client)
    row = rows["10_reminders/over.md"]
    (FOLDER / "over.md").write_text(reminders["over.md"] + "\nedited elsewhere\n", encoding="utf-8")
    import os, time
    os.utime(FOLDER / "over.md", (time.time() + 5, time.time() + 5))
    assert post(client, "/api/reminder/done", {"path": "10_reminders/over.md", "mtime": row["mtime"]}).status_code == 409


def test_occurrences_for_the_calendar(client, reminders):
    """D7: /api/data carries the current month ±1; /api/occurrences serves any range
    up to three months; a multi-day window is one row per day with its span."""
    d = client.get("/api/data").json()
    o = d["occurrences"]
    first = dt.date(TODAY.year, TODAY.month, 1)
    assert o["from"] == (first - dt.timedelta(days=1)).replace(day=1).isoformat()
    assert all(it["kind"] in ("event", "reminder") for it in o["items"])
    mine = [it for it in o["items"] if it["path"] == "10_reminders/over.md"]
    assert mine and all(it["state"] in ("done", "overdue", "open", "upcoming") for it in mine)
    assert any(it["state"] == "overdue" for it in mine)
    # a two-day monthly window, asked for explicitly
    p = FOLDER / "two.md"
    p.write_text(reminder("2026-01-01", "[15, 16]"), encoding="utf-8")
    try:
        r = client.get("/api/occurrences?from=2026-03-01&to=2026-03-31").json()
        rows = [it for it in r["items"] if it["path"] == "10_reminders/two.md"]
        assert [(it["date"], it["span"]) for it in rows] == [("2026-03-15", "1/2"), ("2026-03-16", "2/2")]
        # clamp at the month's end: [31] in February is the 28th
        p.write_text(reminder("2026-01-01", "[31]"), encoding="utf-8")
        r = client.get("/api/occurrences?from=2026-02-01&to=2026-02-28").json()
        assert [it["date"] for it in r["items"] if it["path"] == "10_reminders/two.md"] == ["2026-02-28"]
        # events come before reminders on the same day; invalid ranges are refused
        assert client.get("/api/occurrences?from=2026-01-01&to=2026-12-31").status_code == 400
        assert client.get("/api/occurrences?from=2026-02-10&to=2026-02-01").status_code == 400
        assert client.get("/api/occurrences?from=x&to=y").status_code == 400
    finally:
        p.unlink()


def test_done_adds_the_missed_windows_to_missed(client):
    """D6: Done writes `last_done` and adds the windows that passed undone (the
    latest passed one excepted) to `missed`; nothing else changes."""
    FOLDER.mkdir(exist_ok=True)
    p = FOLDER / "missed.md"
    start = (TODAY - dt.timedelta(days=100)).replace(day=1)
    text = ("---\ntype: reminder\nvisibility: private\ncircle: work\n"
            f"date: {start.isoformat()}\nuntil:\nrepeat: monthly\ndays: [1]\nlast_done:\nmissed: 0\nstatus: active\n---\n# M\n")
    p.write_text(text, encoding="utf-8")
    try:
        item = client.get("/api/item?path=10_reminders/missed.md").json()
        r = post(client, "/api/reminder/done", {"path": "10_reminders/missed.md", "mtime": item["mtime"]})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["missed_added"] >= 1 and body["missed"] == body["missed_added"]
        after = p.read_text(encoding="utf-8")
        assert f"last_done: {TODAY.isoformat()}" in after and f"missed: {body['missed']}" in after
        changed = [a for a, b in zip(text.splitlines(), after.splitlines()) if a != b]
        assert len(changed) == 2
        # a second Done the same day: nothing new is missed, missed stays
        item = client.get("/api/item?path=10_reminders/missed.md").json()
        r = post(client, "/api/reminder/done", {"path": "10_reminders/missed.md", "mtime": item["mtime"]})
        assert r.status_code == 200 and r.json()["missed_added"] == 0 and r.json()["missed"] == body["missed"]
    finally:
        p.unlink()


def test_today_lists_overdue_reminders_and_the_tile_counts_them(client, reminders):
    d = client.get("/api/data").json()
    late = [e for e in d["upcoming"] if e["kind"] == "reminder" and e["days_left"] < 0]
    assert late and late[0]["path"] == "10_reminders/over.md"
    assert all("mtime" in e for e in late)          # Done on the Today card sends it back
