# -*- coding: utf-8 -*-
"""Persistent SQLite index (metadata table + FTS5 full-text index).

This is a *derived cache* of the .md files — the files stay the single source
of truth. `sync()` compares mtimes and re-parses only what changed, so startup
and refresh stay fast as the folder grows. Deleting data/index.db is always
safe; it is rebuilt on the next start.
"""
import json
import re
import sqlite3
import threading

from . import scanner, security
from .config import DATA_DIR, DB_PATH

_lock = threading.Lock()
_db = None

SCHEMA_VERSION = 7   # bump when columns change; cache is dropped & rebuilt  (4: +visibility; 5: +repeat, days, last_done; 6: lessons.context; 7: +related)

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(
  path     TEXT PRIMARY KEY,
  mtime_ns INTEGER NOT NULL,
  size     INTEGER NOT NULL,
  kind     TEXT, title TEXT, circle TEXT, visibility TEXT,
  date     TEXT, time TEXT, status TEXT, tags TEXT,
  cadence  TEXT, last_contact TEXT, role TEXT, until TEXT,
  energy   INTEGER, q INTEGER,
  q1 INTEGER DEFAULT 0, q2 INTEGER DEFAULT 0,
  q3 INTEGER DEFAULT 0, q4 INTEGER DEFAULT 0,
  repeat   TEXT, days TEXT, last_done TEXT,
  related  TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path UNINDEXED, title, body);
CREATE TABLE IF NOT EXISTS lessons(
  path TEXT NOT NULL, date TEXT, text TEXT NOT NULL, context TEXT
);
CREATE INDEX IF NOT EXISTS idx_files_kind ON files(kind);
CREATE INDEX IF NOT EXISTS idx_files_date ON files(date);
CREATE INDEX IF NOT EXISTS idx_lessons_date ON lessons(date);
"""


def db():
    global _db
    if _db is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
        ver = _db.execute("PRAGMA user_version").fetchone()[0]
        if ver != SCHEMA_VERSION:
            # derived cache: on schema change just drop & rebuild
            for tbl in ("files", "docs", "lessons"):
                _db.execute(f"DROP TABLE IF EXISTS {tbl}")
            _db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        _db.executescript(SCHEMA)
    return _db


def sync():
    """Incremental sync: add/update changed files, drop deleted ones."""
    with _lock:
        con = db()
        disk = scanner.disk_state()
        known = dict(con.execute("SELECT path, mtime_ns FROM files"))
        stale = [p for p in known if p not in disk]
        dirty = [p for p, (_, m, _) in disk.items() if known.get(p) != m]
        for p in stale:
            con.execute("DELETE FROM files WHERE path=?", (p,))
            con.execute("DELETE FROM docs WHERE path=?", (p,))
            con.execute("DELETE FROM lessons WHERE path=?", (p,))
        for p in dirty:
            kind, mtime_ns, size = disk[p]
            row = scanner.parse_file(p, kind)
            con.execute(
                "REPLACE INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (p, mtime_ns, size, row["kind"], row["title"], row["circle"],
                 row["visibility"],
                 row["date"], row["time"], row["status"], row["tags"],
                 row["cadence"], row["last_contact"], row["role"], row["until"],
                 row["energy"], row["q"],
                 row["q1"], row["q2"], row["q3"], row["q4"],
                 row["repeat"], row["days"], row["last_done"], row.get("related", "")))
            con.execute("DELETE FROM docs WHERE path=?", (p,))
            con.execute("INSERT INTO docs VALUES (?,?,?)",
                        (p, row["title"], row["body"]))
            con.execute("DELETE FROM lessons WHERE path=?", (p,))
            con.executemany("INSERT INTO lessons VALUES (?,?,?,?)",
                            [(p, d, txt, ctx) for d, txt, ctx in row["lessons"]])
        con.commit()
        return {"updated": len(dirty), "removed": len(stale), "total": len(disk)}


COLS = "path, kind, title, circle, visibility, date, time, status, tags"


def _row(r):
    d = dict(zip(COLS.split(", "), r))
    d["tags"] = [t for t in (d["tags"] or "").split(",") if t]
    return d


def all_items():
    con = db()
    rows = con.execute(
        f"SELECT {COLS} FROM files "
        "ORDER BY (date IS NULL), date DESC, path").fetchall()
    return [_row(r) for r in rows]


def search(q):
    """FTS5 prefix search; returns rows in rank order with highlighted snippets.

    The snippet is built from raw note text, so it is escaped here and only
    our own highlight markers become <mark> (security.safe_snippet)."""
    tokens = re.findall(r"\w+", q, re.UNICODE)
    if not tokens:
        return []
    match = " ".join(f'"{t}"*' for t in tokens)
    con = db()
    rows = con.execute(
        "SELECT f.path, f.kind, f.title, f.circle, f.visibility, f.date, f.time, f.status, f.tags, "
        "snippet(docs, 2, ?, ?, ' … ', 14) "
        "FROM docs JOIN files f ON f.path = docs.path "
        "WHERE docs MATCH ? ORDER BY rank LIMIT 200",
        (security.SNIP_OPEN, security.SNIP_CLOSE, match)).fetchall()
    out = []
    for r in rows:
        d = _row(r[:9])
        d["snippet"] = security.safe_snippet(r[9])
        out.append(d)
    return out


def _split(csv):
    return [t for t in (csv or "").split(",") if t]


def tag_counts():
    """Every tag with how many items carry it, open and in all — the sidebar's Tags
    section and the Browse filter (Round 002). Most open first."""
    from aicowork_core.common import is_open
    con = db()
    counts = {}
    for tags, status in con.execute("SELECT tags, status FROM files WHERE tags != ''"):
        for t in set(_split(tags)):
            c = counts.setdefault(t, {"tag": t, "open": 0, "all": 0})
            c["all"] += 1
            c["open"] += 1 if is_open(status) else 0
    return sorted(counts.values(), key=lambda c: (-c["open"], -c["all"], c["tag"]))


def related(path, limit=20):
    """Items linked to `path`: what its `related:` points at, what points at it, and
    open items sharing a tag (newest first). Each row says why."""
    from aicowork_core.common import is_open
    con = db()
    me = con.execute("SELECT tags, related FROM files WHERE path=?", (path,)).fetchone()
    if not me:
        return []
    my_tags, my_rel = set(_split(me[0])), _split(me[1])
    rows = con.execute(f"SELECT {COLS}, related FROM files WHERE path != ? AND (tags != '' OR related != '')",
                       (path,)).fetchall()
    by_path = {r[0]: r for r in rows}
    out, seen = [], {path}

    def add(r, why):
        d = _row(r[:-1])
        if d["path"] not in seen:
            seen.add(d["path"])
            d["why"] = why
            out.append(d)
    for p in my_rel:
        if p in by_path:
            add(by_path[p], "related:")
        elif p not in seen:
            seen.add(p)
            out.append({"path": p, "kind": None, "title": p, "status": None, "date": None, "tags": [], "why": "related: — not found"})
    for r in rows:
        if path in _split(r[-1]):
            add(r, "points here")
    shared = [(r, my_tags & set(_split(r[8]))) for r in rows]
    for r, s in sorted((x for x in shared if x[1] and is_open(x[0][7])), key=lambda x: (x[0][5] or ""), reverse=True):
        add(r, "#" + " #".join(sorted(s)))
    return out[:limit]


def open_counts():
    """Items per kind that are not closed (config.CLOSED_STATUSES): what the sidebar
    shows, so a done project or an archived note does not keep counting."""
    from .config import CLOSED_STATUSES
    con = db()
    marks = ",".join("?" * len(CLOSED_STATUSES))
    return dict(con.execute(
        f"SELECT kind, COUNT(*) FROM files WHERE status IS NULL OR status = '' "
        f"OR lower(status) NOT IN ({marks}) GROUP BY kind", sorted(CLOSED_STATUSES)))


def counts_and_balance(circles, content_kinds):
    con = db()
    counts = dict(con.execute("SELECT kind, COUNT(*) FROM files GROUP BY kind"))
    balance = {c: {k: 0 for k in content_kinds} for c in circles}
    unassigned = 0
    for kind, circle, n in con.execute(
            "SELECT kind, circle, COUNT(*) FROM files GROUP BY kind, circle"):
        if kind not in content_kinds:
            continue
        if circle in balance:
            balance[circle][kind] += n
        else:
            unassigned += n
    return counts, balance, unassigned


def events():
    con = db()
    rows = con.execute(
        f"SELECT {COLS} FROM files WHERE kind='event' AND date IS NOT NULL "
        "ORDER BY date").fetchall()
    return [_row(r) for r in rows]


# ---------- v1.2 derived signals ----------

def overdue_contacts(today):
    """Personas with cadence + last_contact where the cadence window has passed."""
    from .config import CADENCE_DAYS
    import datetime as dt
    out = []
    for r in db().execute(
            "SELECT path, title, circle, cadence, last_contact, visibility FROM files "
            "WHERE kind='persona' AND cadence IS NOT NULL"):
        path, title, circle, cadence, last, vis = r
        days = CADENCE_DAYS.get(cadence)
        if not days:
            continue
        last_d = scanner.parse_date(last) if last else None
        overdue = (today - last_d).days - days if last_d else None
        if overdue is None or overdue > 0:
            out.append({"path": path, "title": title, "circle": circle,
                        "cadence": cadence, "last_contact": last,
                        "visibility": vis, "overdue_days": overdue})
    out.sort(key=lambda x: -(x["overdue_days"] if x["overdue_days"] is not None else 9999))
    return out


def practices():
    rows = db().execute(
        "SELECT path, title, circle, cadence, status, date, until, visibility FROM files "
        "WHERE kind='practice' ORDER BY circle, title").fetchall()
    return [dict(zip(("path", "title", "circle", "cadence", "status",
                      "start", "until", "visibility"), r)) for r in rows]


def reminders(today, horizon_days):
    """Reminders to show in "Keep an eye", with their computed state (recur.state);
    paused, done, invalid and far-off ones are left out. Nothing is stored but
    the file's own fields, so a rebuilt cache gives the same answer."""
    from aicowork_core import recur
    out = []
    for r in db().execute(
            "SELECT path, title, circle, visibility, status, date, until, repeat, days, last_done, mtime_ns "
            "FROM files WHERE kind='reminder' AND repeat IS NOT NULL"):
        path, title, circle, vis, status, date, until, repeat, days, last_done, mtime_ns = r
        try:
            days = json.loads(days) if days else None
        except ValueError:
            days = None
        meta = {"date": date, "until": until, "repeat": repeat, "last_done": last_done,
                "status": status, "days": days}
        s = recur.state(recur.parse_rule(meta), today, horizon_days)
        if s:
            out.append(dict(s, path=path, title=title, circle=circle, visibility=vis,
                            repeat=repeat, last_done=last_done, mtime=mtime_ns / 1e9))
    return out


def occurrences(start, end, today):
    """Everything dated in [start, end] for the calendar: events by their date, and
    each reminder's windows (CONVENTIONS "Reminders", rule 2) — one row per day of a
    window, with `span` "i/n" when a window covers several days and a `state`:
    done (first <= last_done), overdue (open and last < today), open (the window
    includes today or has started), upcoming. Computed from the files' fields;
    nothing is stored (D7, plan 2 of 2026-10-06)."""
    import datetime as dt
    from aicowork_core import recur
    rows = []
    for r in db().execute(
            f"SELECT {COLS} FROM files WHERE kind='event' AND date >= ? AND date <= ? ORDER BY date, time",
            (start.isoformat(), end.isoformat())):
        rows.append(dict(_row(r), state=None, span=None))
    for r in db().execute(
            "SELECT path, title, circle, visibility, status, date, until, repeat, days, last_done "
            "FROM files WHERE kind='reminder' AND repeat IS NOT NULL"):
        path, title, circle, vis, status, date, until, repeat, days, last_done = r
        try:
            days = json.loads(days) if days else None
        except ValueError:
            days = None
        rule = recur.parse_rule({"date": date, "until": until, "repeat": repeat, "last_done": last_done,
                                 "status": status, "days": days})
        if rule is None or rule.status != "active":
            continue
        for first, last in recur.windows(rule, start, end):
            n = (last - first).days + 1
            if rule.last_done and rule.last_done >= first:
                state = "done"
            elif last < today:
                state = "overdue"
            elif first <= today:
                state = "open"
            else:
                state = "upcoming"
            for i in range(n):
                d = first + dt.timedelta(days=i)
                if start <= d <= end:
                    rows.append({"path": path, "kind": "reminder", "title": title, "circle": circle,
                                 "visibility": vis, "date": d.isoformat(), "time": None, "status": status,
                                 "tags": [], "state": state, "span": f"{i + 1}/{n}" if n > 1 else None})
    rows.sort(key=lambda x: (x["date"], x["kind"] == "reminder", x["time"] or "", x["title"]))
    return rows


def q_stats(since_date):
    """Quadrant tallies from inline #q tags in daily logs since a date.
    Returns {'q1':n,...,'q2_pct': float|None}."""
    r = db().execute(
        "SELECT COALESCE(SUM(q1),0), COALESCE(SUM(q2),0), "
        "COALESCE(SUM(q3),0), COALESCE(SUM(q4),0) FROM files "
        "WHERE kind='log' AND date >= ?", (str(since_date),)).fetchone()
    total = sum(r)
    return {"q1": r[0], "q2": r[1], "q3": r[2], "q4": r[3],
            "q2_pct": round(100 * r[1] / total) if total else None}


def recent_lessons(limit=30):
    rows = db().execute(
        "SELECT l.date, l.text, l.path, f.circle, l.context FROM lessons l "
        "LEFT JOIN files f ON f.path = l.path "
        "ORDER BY (l.date=''), l.date DESC LIMIT ?", (limit,)).fetchall()
    return [dict(zip(("date", "text", "path", "circle", "context"), r)) for r in rows]


def lessons_total():
    """Total lesson lines indexed - lets the UI say "3 of 42" honestly."""
    return db().execute("SELECT COUNT(*) FROM lessons").fetchone()[0]


def on_this_day(today):
    """Resurfacing: items dated exactly 1/3/12 months ago (approx, same day-of-month)."""
    import datetime as dt
    targets = []
    for months in (1, 3, 12):
        y, m = today.year, today.month - months
        while m <= 0:
            y, m = y - 1, m + 12
        try:
            targets.append((months, dt.date(y, m, today.day).isoformat()))
        except ValueError:
            continue   # e.g. no 31st that month
    out = []
    for months, d in targets:
        for r in db().execute(
                f"SELECT {COLS} FROM files WHERE date = ? AND kind != 'note'", (d,)):
            out.append(dict(_row(r), months_ago=months))
        # lessons of that day too (E8): a lesson resurfaces with its source
        for date, text, path, circle, ctx in db().execute(
                "SELECT l.date, l.text, l.path, f.circle, l.context FROM lessons l "
                "LEFT JOIN files f ON f.path = l.path WHERE l.date = ?", (d,)):
            out.append({"path": path, "kind": "lesson", "title": text, "circle": circle, "visibility": "private",
                        "date": date, "time": None, "status": None, "tags": [], "context": ctx, "months_ago": months})
    return out


def energy_series(since_date):
    rows = db().execute(
        "SELECT date, energy FROM files WHERE kind='log' AND energy IS NOT NULL "
        "AND date >= ? ORDER BY date", (str(since_date),)).fetchall()
    return [{"date": d, "energy": e} for d, e in rows]
