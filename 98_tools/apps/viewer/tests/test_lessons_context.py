# -*- coding: utf-8 -*-
"""Lessons with a source (rc.6, E8): the trailing [context] of a #lesson line is a
path when it names an existing file in the folder; lessons resurface on this day."""
import datetime as dt

import pytest
from fastapi.testclient import TestClient

from conftest import BASE
from viewer import api, scanner
from viewer.config import PORT

ORIGIN = f"http://127.0.0.1:{PORT}"


@pytest.fixture
def client():
    c = TestClient(api.app, base_url=ORIGIN)
    c.get(f"/?t={api.TOKEN}", follow_redirects=False)
    c.cookies.set(api.COOKIE, api.TOKEN)
    return c


def test_lesson_context_is_a_path_only_when_the_file_exists(tmp_path):
    (tmp_path / "04_projects" / "x").mkdir(parents=True)
    (tmp_path / "04_projects" / "x" / "index.md").write_text("# x\n", encoding="utf-8")
    body = ("- #lesson A risk hides in the acceptance criteria. [04_projects/x/index.md]\n"
            "- #lesson A label stays a label. [project-x]\n"
            "- #lesson Nothing outside the folder. [../secret.md]\n"
            "- #lesson Absolute paths never. [/etc/passwd]\n"
            "<!-- #lesson an instruction in a comment is not a lesson [x] -->\n")
    rows = scanner.lessons(body, "2026-03-01", tmp_path)
    assert rows[0] == ("2026-03-01", "A risk hides in the acceptance criteria.", "04_projects/x/index.md")
    assert rows[1] == ("2026-03-01", "A label stays a label. [project-x]", None)
    assert rows[2][2] is None and rows[3][2] is None and len(rows) == 4
    assert scanner.lessons(body, "2026-03-01")[0][2] is None            # no base: never a path


def test_lessons_served_with_context_and_on_this_day(client):
    today = dt.date.today()
    y, m = today.year, today.month - 1
    if m == 0:
        y, m = y - 1, 12
    try:
        a_month_ago = dt.date(y, m, today.day)
    except ValueError:
        pytest.skip("no such day a month ago")
    log = BASE / "06_logs" / "daily" / f"{a_month_ago.isoformat()}.md"
    log.write_text(f"---\ntype: log\ncircle: work\ndate: {a_month_ago.isoformat()}\nvisibility: private\n---\n"
                   "# Day\n\n## 💡 Insights\n- #lesson Say the risk out loud. [01_events/2026-01-01_hello.md]\n",
                   encoding="utf-8")
    try:
        d = client.get("/api/data").json()
        ls = [l for l in d["lessons"] if l["path"].endswith(f"{a_month_ago.isoformat()}.md")]
        assert ls and ls[0]["context"] == "01_events/2026-01-01_hello.md"
        otd = [i for i in d["on_this_day"] if i["kind"] == "lesson"]
        assert otd and otd[0]["months_ago"] == 1 and otd[0]["context"] == "01_events/2026-01-01_hello.md"
        assert otd[0]["title"] == "Say the risk out loud."
    finally:
        log.unlink()
