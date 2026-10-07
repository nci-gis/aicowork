# -*- coding: utf-8 -*-
"""Reminders: the occurrence rules of CONVENTIONS "Reminders", table-driven."""
import datetime as dt

import pytest

from aicowork_core.frontmatter import parse_frontmatter, set_field
from aicowork_core.recur import parse_rule, state, validate, windows

D = dt.date.fromisoformat


def meta(repeat="monthly", days=("15", "16"), date="2026-10-06", **kw):
    m = {"type": "reminder", "circle": "work", "date": date, "repeat": repeat,
         "days": list(days) if isinstance(days, (list, tuple)) else days}
    m.update(kw)
    return m


def st(m, today, horizon=14):
    return state(parse_rule(m), D(today), horizon)


@pytest.mark.parametrize("m,today,expected", [
    # upcoming: first 10-15, 9 days left
    (meta(), "2026-10-06", {"state": "upcoming", "first": "2026-10-15", "last": "2026-10-16", "days_left": 9}),
    # due on day 1 and on day 2 of the window
    (meta(), "2026-10-15", {"state": "due", "first": "2026-10-15", "last": "2026-10-16"}),
    (meta(), "2026-10-16", {"state": "due", "first": "2026-10-15", "last": "2026-10-16"}),
    # overdue: 4 days after the window's last day, one window missed
    (meta(), "2026-10-20", {"state": "overdue", "first": "2026-10-15", "last": "2026-10-16",
                            "days_over": 4, "missed": 1}),
    # done on the first day closes the window; the next one is a month away
    (meta(last_done="2026-10-15"), "2026-11-10",
     {"state": "upcoming", "first": "2026-11-15", "last": "2026-11-16", "days_left": 5}),
    # two windows in one month: [1] and [15]; the 10-01 one is open
    (meta(days=["1", "15"], date="2026-09-20"), "2026-10-10",
     {"state": "overdue", "first": "2026-10-01", "last": "2026-10-01", "days_over": 9, "missed": 1}),
    # until inclusive: a window starting on `until` counts
    (meta(until="2026-10-15"), "2026-10-15", {"state": "due", "first": "2026-10-15", "last": "2026-10-16"}),
    # expired: until passed, nothing open
    (meta(until="2026-10-31", last_done="2026-10-16"), "2026-11-02", {"state": "expired", "until": "2026-10-31"}),
    # several missed windows are counted
    (meta(date="2026-08-01"), "2026-10-20", {"state": "overdue", "first": "2026-08-15", "last": "2026-08-16",
                                             "days_over": 65, "missed": 3}),
])
def test_states(m, today, expected):
    assert st(m, today) == expected


def test_not_shown_outside_horizon():
    assert st(meta(), "2026-10-06", horizon=5) is None
    assert st(meta(), "2026-10-06", horizon=9)["state"] == "upcoming"


def test_paused_and_done_are_not_computed():
    assert st(meta(status="paused"), "2026-10-15") is None
    assert st(meta(status="done"), "2026-10-15") is None


def test_no_end_still_computed_years_later():
    r = st(meta(last_done="2031-10-16"), "2031-11-10")
    assert r == {"state": "upcoming", "first": "2031-11-15", "last": "2031-11-16", "days_left": 5}


def test_clamp_month_end_and_leap_day():
    r = parse_rule(meta(days=["31"], date="2026-01-01", last_done="2026-01-31"))
    assert state(r, D("2026-02-10"), 30)["first"] == "2026-02-28"
    r = parse_rule(meta(repeat="yearly", days=["02-29"], date="2026-01-01", last_done="2026-02-28"))
    assert state(r, D("2027-02-01"), 30)["first"] == "2027-02-28"
    r = parse_rule(meta(repeat="yearly", days=["02-29"], date="2027-03-01"))
    assert state(r, D("2028-02-20"), 30)["first"] == "2028-02-29"


def test_clamped_duplicates_collapse():
    r = parse_rule(meta(days=["30", "31"], date="2026-02-01"))
    assert windows(r, D("2026-02-01"), D("2026-02-28")) == [(D("2026-02-28"), D("2026-02-28"))]


def test_window_never_crosses_a_period():
    r = parse_rule(meta(days=["31", "1"], date="2026-10-01"))
    assert windows(r, D("2026-10-01"), D("2026-11-30")) == [
        (D("2026-10-01"), D("2026-10-01")), (D("2026-10-31"), D("2026-10-31")),
        (D("2026-11-01"), D("2026-11-01")), (D("2026-11-30"), D("2026-11-30"))]


def test_weekly_weekend_is_one_window():
    r = parse_rule(meta(repeat="weekly", days=["sat", "sun"], date="2026-10-05"))
    # 2026-10-07 is a Wednesday
    assert state(r, D("2026-10-07"), 14) == {"state": "upcoming", "first": "2026-10-10",
                                             "last": "2026-10-11", "days_left": 3}


def test_single_value_without_brackets():
    assert st(meta(days="15"), "2026-10-15")["state"] == "due"
    assert st(meta(repeat="weekly", days="thu"), "2026-10-08")["state"] == "due"


def test_yearly_two_days():
    m = meta(repeat="yearly", days=["03-31", "09-30"], date="2026-01-01", last_done="2026-03-31")
    assert st(m, "2026-09-20")["first"] == "2026-09-30"


@pytest.mark.parametrize("m,needle", [
    (meta(days=["0"]), "monthly `days` takes 1…31"),
    (meta(days=["32"]), "monthly `days` takes 1…31"),
    (meta(repeat="weekly", days=["15"]), "weekly `days` takes mon…sun"),
    (meta(repeat="yearly", days=["13-01"]), 'yearly `days` takes "MM-DD"'),
    (meta(repeat="yearly", days=["02-30"]), 'yearly `days` takes "MM-DD"'),
    (meta(repeat="daily"), "repeat 'daily' is not one of"),
    (meta(days=[]), "`days` is empty"),
    (meta(until="2026-10-01"), "`until` 2026-10-01 is before `date`"),
    (meta(last_done="15/10"), "`last_done` '15/10' is not a date"),
    (meta(status="later"), "status 'later' is not one of"),
])
def test_invalid(m, needle):
    msgs = validate(m)
    assert any(needle in x for x in msgs), msgs
    assert parse_rule(m) is None
    assert state(parse_rule(m), D("2026-10-15"), 14) is None


def test_on_instead_of_days():
    m = meta()
    m["on"] = m.pop("days")
    assert any("use `days`, not `on`" in x for x in validate(m))
    assert parse_rule(m) is None


def test_valid_reminder_has_no_messages():
    assert validate(meta()) == []
    assert validate(meta(repeat="weekly", days=["MON", "thu"])) == []


def test_parsed_from_a_file():
    text = ('---\ntype: reminder\nvisibility: private\ncircle: work\ndate: 2026-10-06\nuntil:\n'
            'repeat: monthly\ndays: [15, 16]\nlast_done:\nstatus: active\n---\n# Check the account\n')
    m, _ = parse_frontmatter(text)
    assert validate(m) == []
    assert st(m, "2026-10-06")["days_left"] == 9


@pytest.mark.parametrize("text,expected", [
    # present, LF
    ("---\ntype: reminder\nlast_done: 2026-09-16\nstatus: active\n---\n# T\n",
     "---\ntype: reminder\nlast_done: 2026-10-15\nstatus: active\n---\n# T\n"),
    # empty value with a comment: the comment and its spacing stay
    ("---\nlast_done:   # set by Done\n---\n", "---\nlast_done: 2026-10-15   # set by Done\n---\n"),
    ("---\nlast_done: 2026-09-16 # c\n---\n", "---\nlast_done: 2026-10-15 # c\n---\n"),
    # absent: inserted before the closing fence
    ("---\ntype: reminder\n---\nbody\n", "---\ntype: reminder\nlast_done: 2026-10-15\n---\nbody\n"),
    # CRLF kept, present and absent
    ("---\r\nlast_done: 2026-09-16\r\nx: 1\r\n---\r\nb\r\n", "---\r\nlast_done: 2026-10-15\r\nx: 1\r\n---\r\nb\r\n"),
    ("---\r\nx: 1\r\n---\r\nb\r\n", "---\r\nx: 1\r\nlast_done: 2026-10-15\r\n---\r\nb\r\n"),
    # a longer key with the same prefix and a nested key are not touched
    ("---\nlast_done_by: me\nm:\n  last_done: x\n---\n", "---\nlast_done_by: me\nm:\n  last_done: x\nlast_done: 2026-10-15\n---\n"),
])
def test_set_field(text, expected):
    assert set_field(text, "last_done", "2026-10-15") == expected


def test_set_field_needs_frontmatter():
    with pytest.raises(ValueError):
        set_field("# no frontmatter\n", "last_done", "2026-10-15")
    with pytest.raises(ValueError):
        set_field("---\nx: 1\n", "last_done", "2026-10-15")


def test_very_old_start_says_the_missed_count_is_capped():
    r = st(meta(repeat="weekly", days=["mon"], date="1980-01-07"), "2026-10-06")
    assert r["state"] == "overdue" and r["first"] == "1980-01-07"
    assert r.get("missed_capped") is True and r["missed"] >= 1000
    r = st(meta(repeat="weekly", days=["mon"], date="2000-01-03"), "2026-10-06")
    assert "missed_capped" not in r and r["missed"] == 1397


def test_three_digit_day_is_invalid():
    assert any("1…31" in m for m in validate(meta(days=["015"])))


@pytest.mark.parametrize("text,expected", [
    # fences with trailing spaces are fences, as the parser reads them
    ("--- \nx: 1\n--- \nbody\n---\n", "--- \nx: 1\nlast_done: 2026-10-15\n--- \nbody\n---\n"),
])
def test_set_field_reads_fences_like_the_parser(text, expected):
    assert set_field(text, "last_done", "2026-10-15") == expected
    assert parse_frontmatter(expected)[0]["last_done"] == "2026-10-15"


@pytest.mark.parametrize("last_done,done,expected", [
    # monthly [15,16] from 2026-08-01; Done on 11-20 closes 08, 09, 10, 11: 11 done late, three missed
    ("", "2026-11-20", 3),
    # the window being closed on time: nothing missed
    ("", "2026-08-16", 0),
    # one window passed before: it is the "late" one, not missed
    ("", "2026-08-20", 0),
    # two passed: the earlier one missed
    ("", "2026-09-20", 1),
    # done last month, this one late: nothing missed
    ("2026-09-15", "2026-10-20", 0),
    # done before the first window: nothing to count
    ("", "2026-08-10", 0),
])
def test_done_increment(last_done, done, expected):
    from aicowork_core.recur import done_increment
    r = parse_rule(meta(date="2026-08-01", last_done=last_done))
    assert done_increment(r, D(done)) == expected
