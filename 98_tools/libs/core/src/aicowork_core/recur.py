# -*- coding: utf-8 -*-
"""Reminders: when a repeating duty is due. Pure functions, standard library only.

The rules are CONVENTIONS "Reminders"; this module is one implementation of
them. A reminder's only state is `last_done`: everything else (upcoming, due,
overdue, missed, expired) is computed from the file and today's date, never
stored, so deleting every cache gives the same answer.

    repeat: weekly | monthly | yearly
    days:   weekly  -> mon..sun        e.g. [mon, thu]
            monthly -> 1..31           e.g. [15, 16]
            yearly  -> "MM-DD"         e.g. ["03-31", "09-30"]
"""
import calendar
import datetime as dt
from collections import namedtuple

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
REPEATS = ("weekly", "monthly", "yearly")
STATUSES = ("active", "paused", "done")
MAX_PERIODS = 2000           # guard: never walk more periods than this in one call (~38 years weekly)

# repeat: str; days: tuple of ints (weekday 0-6 / day 1-31) or (month, day) pairs;
# start, until, last_done: date or None; status: active | paused | done
Rule = namedtuple("Rule", "repeat days start until last_done status notice")


def _date(v):
    if v in (None, ""):
        return None
    try:
        return dt.date.fromisoformat(str(v).strip()[:10]) if len(str(v).strip()) == 10 else None
    except ValueError:
        return None


def _items(v):
    """`days: 15` and `days: [15, 16]` are both accepted."""
    if v in (None, ""):
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _day_item(repeat, x):
    """-> (normalised value, None) or (None, message)."""
    s = str(x).strip().lower()
    if repeat == "weekly":
        if s in WEEKDAYS:
            return WEEKDAYS.index(s), None
        return None, f"weekly `days` takes mon…sun, not {x!r}"
    if repeat == "monthly":
        if s.isdigit() and len(s) <= 2 and 1 <= int(s) <= 31:
            return int(s), None
        return None, f"monthly `days` takes 1…31, not {x!r}"
    # yearly: "MM-DD", validated against a leap year so 02-29 is allowed
    parts = s.split("-")
    if len(parts) == 2 and all(p.isdigit() and len(p) == 2 for p in parts):
        m, d = int(parts[0]), int(parts[1])
        if 1 <= m <= 12 and 1 <= d <= calendar.monthrange(2024, m)[1]:
            return (m, d), None
    return None, f'yearly `days` takes "MM-DD", not {x!r}'


def validate(meta):
    """Messages for conformance; [] when the reminder fields are usable. Required
    keys are reported by the frontmatter check; this adds what only a reminder needs."""
    out = []
    if "on" in meta and "days" not in meta:
        out.append("use `days`, not `on` (`on:` reads as true in YAML 1.1)")
    repeat = str(meta.get("repeat") or "").strip()
    if repeat and repeat not in REPEATS:
        out.append(f"repeat {repeat!r} is not one of {', '.join(REPEATS)}")
    if "days" in meta and not _items(meta.get("days")):
        out.append("`days` is empty")
    if repeat in REPEATS:
        for x in _items(meta.get("days")):
            _, msg = _day_item(repeat, x)
            if msg:
                out.append(msg)
    for k in ("date", "until", "last_done"):
        v = meta.get(k)
        if v not in (None, "") and _date(v) is None:
            out.append(f"`{k}` {v!r} is not a date YYYY-MM-DD")
    start, until = _date(meta.get("date")), _date(meta.get("until"))
    if start and until and until < start:
        out.append(f"`until` {until} is before `date` {start}")
    status = str(meta.get("status") or "active").strip()
    if status not in STATUSES:
        out.append(f"status {status!r} is not one of {', '.join(STATUSES)}")
    if _notice(meta.get("notice")) is False:
        out.append(f"`notice` {meta.get('notice')!r} is not a whole number of days")
    return out


def _notice(v):
    """-> int ≥ 0, None when unset, False when invalid."""
    if v in (None, ""):
        return None
    s = str(v).strip()
    return int(s) if s.isdigit() else False


def parse_rule(meta):
    """-> Rule, or None when the reminder is not usable (see validate)."""
    if validate(meta):
        return None
    repeat = str(meta.get("repeat") or "").strip()
    start = _date(meta.get("date"))
    items = _items(meta.get("days"))
    if repeat not in REPEATS or start is None or not items:
        return None
    days = tuple(sorted({_day_item(repeat, x)[0] for x in items}))
    return Rule(repeat, days, start, _date(meta.get("until")), _date(meta.get("last_done")),
                str(meta.get("status") or "active").strip(), _notice(meta.get("notice")))


# ---------------- occurrence maths ----------------

def _period_start(repeat, d):
    if repeat == "weekly":
        return d - dt.timedelta(days=d.weekday())
    if repeat == "monthly":
        return d.replace(day=1)
    return d.replace(month=1, day=1)


def _next_period(repeat, p):
    if repeat == "weekly":
        return p + dt.timedelta(days=7)
    if repeat == "monthly":
        return (p.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return p.replace(year=p.year + 1)


def _dates_in_period(rule, p):
    """The rule's dates inside one period, clamped (rule 1), sorted, unique."""
    if rule.repeat == "weekly":
        out = {p + dt.timedelta(days=w) for w in rule.days}
    elif rule.repeat == "monthly":
        last = calendar.monthrange(p.year, p.month)[1]
        out = {p.replace(day=min(d, last)) for d in rule.days}
    else:
        out = set()
        for m, d in rule.days:
            last = calendar.monthrange(p.year, m)[1]
            out.add(dt.date(p.year, m, min(d, last)))
    return sorted(out)


def _group(dates):
    """Consecutive dates -> windows [first, last] (rule 2)."""
    wins = []
    for d in dates:
        if wins and d - wins[-1][1] == dt.timedelta(days=1):
            wins[-1][1] = d
        else:
            wins.append([d, d])
    return [tuple(w) for w in wins]


def _walk(rule, start, end):
    """-> (windows, capped): windows whose first day lies in [start, end] and in
    the rule's range (rule 3), sorted; capped is True when MAX_PERIODS stopped
    the walk before `end`."""
    lo = max(start, rule.start)
    hi = min(end, rule.until) if rule.until else end
    out, p, n = [], _period_start(rule.repeat, lo), 0
    while p <= hi and n < MAX_PERIODS:
        for w in _group(_dates_in_period(rule, p)):
            if lo <= w[0] <= hi:
                out.append(w)
        p, n = _next_period(rule.repeat, p), n + 1
    return out, p <= hi


def windows(rule, start, end):
    """Windows whose first day lies in [start, end] and inside the rule's range
    (rule 3), sorted. Walks periods from `start`, never from the rule's origin."""
    return _walk(rule, start, end)[0]


def state(rule, today, horizon_days):
    """-> dict for "Keep an eye", or None when nothing is to be shown (rules 4–8).

    {"state": "upcoming", "first", "last", "days_left"}
    {"state": "due",      "first", "last"}
    {"state": "overdue",  "first", "last", "days_over", "missed"[, "missed_capped": True]}
    {"state": "expired",  "until"}
    Dates are ISO strings."""
    if rule is None or rule.status != "active":
        return None
    lo = rule.start
    if rule.last_done and rule.last_done + dt.timedelta(days=1) > lo:
        lo = rule.last_done + dt.timedelta(days=1)
    # rule 8: an upcoming window is shown within `notice` days of `first` when set, else within the horizon
    ahead = rule.notice if rule.notice is not None else max(int(horizon_days), 0)
    hi = today + dt.timedelta(days=ahead)
    wins, capped = _walk(rule, lo, hi)
    open_ = [w for w in wins if rule.last_done is None or rule.last_done < w[0]]
    if not open_:
        if rule.until and rule.until < today:
            return {"state": "expired", "until": rule.until.isoformat()}
        return None
    first, last = open_[0]
    out = {"first": first.isoformat(), "last": last.isoformat()}
    if today < first:
        return {"state": "upcoming", **out, "days_left": (first - today).days}
    if today <= last:
        return {"state": "due", **out}
    missed = sum(1 for w in open_ if w[1] < today)
    res = {"state": "overdue", **out, "days_over": (today - last).days, "missed": missed}
    if capped and open_[-1][1] < today:
        res["missed_capped"] = True          # at least `missed`: the walk stopped early
    return res


def done_increment(rule, done):
    """Rule 9: how many windows Done on `done` closes without their having been done —
    the windows that passed (last < done) and were open, the latest of them
    excepted (that one was done late, not missed). Pure; a date before the first
    window gives 0."""
    if rule is None:
        return 0
    lo = rule.start
    if rule.last_done and rule.last_done + dt.timedelta(days=1) > lo:
        lo = rule.last_done + dt.timedelta(days=1)
    wins, _ = _walk(rule, lo, done)
    passed = [w for w in wins if w[1] < done and (rule.last_done is None or rule.last_done < w[0])]
    return max(len(passed) - 1, 0) if passed else 0


def check_done_date(rule_or_meta, done, today):
    """A `last_done` value the owner may set: <= today and >= `date`. -> message or None."""
    start = rule_or_meta.start if isinstance(rule_or_meta, Rule) else _date(rule_or_meta.get("date"))
    if done > today:
        return f"{done} is in the future"
    if start and done < start:
        return f"{done} is before the reminder starts ({start})"
    return None
