# -*- coding: utf-8 -*-
"""A triage plan moves a note the agent prepared; the owner only applies it."""
import pytest

from aicowork_core import triage_plan as tp


def _base(tmp_path):
    base = tmp_path / "inst"
    for d in ("00_inbox", "07_archive", "09_decisions"):
        (base / d).mkdir(parents=True)
    return base


def test_a_raw_inbox_item_cannot_be_filed_as_a_note(tmp_path):
    """Found on 2026-10-09: a plan moved a one-line idea into 09_decisions/ as it was,
    and L1-FRONTMATTER failed on the result. The plan carries a type; the file must too."""
    base = _base(tmp_path)
    (base / "00_inbox" / "idea.md").write_text("Idea: try a standing desk.\n", encoding="utf-8")
    plan = {"moves": [{"from": "00_inbox/idea.md", "to": "09_decisions/2026-10-09_standing-desk.md",
                       "type": "decision", "circle": "health"}]}
    with pytest.raises(tp.PlanError, match="no frontmatter with a type"):
        tp.check_plan(base, plan)


def test_a_prepared_note_moves_and_a_raw_item_may_be_archived(tmp_path):
    base = _base(tmp_path)
    (base / "00_inbox" / "idea.md").write_text(
        "---\ntype: decision\nvisibility: private\ncircle: health\ndate: 2026-10-09\n---\n# Standing desk\n",
        encoding="utf-8")
    (base / "00_inbox" / "clip.txt").write_text("a clipping\n", encoding="utf-8")
    plan = {"moves": [{"from": "00_inbox/idea.md", "to": "09_decisions/2026-10-09_standing-desk.md"},
                      {"from": "00_inbox/clip.txt", "to": "07_archive/clip.txt", "note": "stale"}]}
    assert len(tp.check_plan(base, plan)) == 2


def test_applying_a_plan_sets_the_last_triage_footer(tmp_path):
    """inbox-triage Acceptance: a session that ends with a plan leaves the footer;
    applying the plan finishes the triage, so the footer becomes today. Only that
    line changes, and CRLF stays CRLF."""
    from aicowork_core import common as C
    base = _base(tmp_path)
    (base / "06_logs" / "triage").mkdir(parents=True)
    (base / "INDEX.md").write_bytes(b"# INDEX\r\n\r\n## Decisions\r\n\r\n---\r\nLast triage: 2026-01-01\r\n")
    (base / "00_inbox" / "idea.md").write_text(
        "---\ntype: decision\nvisibility: private\ncircle: health\ndate: 2026-10-09\n---\n# Standing desk\n",
        encoding="utf-8")
    plan = base / "06_logs" / "triage" / "2026-10-09_1_plan.json"
    plan.write_text('{"moves": [{"from": "00_inbox/idea.md", "to": "09_decisions/2026-10-09_standing-desk.md"}]}',
                    encoding="utf-8")
    moves, report = tp.apply(base, plan, do_apply=True)
    assert len(moves) == 1 and report
    raw = (base / "INDEX.md").read_bytes()
    assert b"Last triage: " + C.today().isoformat().encode() + b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert raw.startswith(b"# INDEX\r\n\r\n## Decisions")
