# -*- coding: utf-8 -*-
"""FastAPI app: JSON API + static web UI.

Loopback-only by design. Every request passes `guard`: the Host header must be
127.0.0.1/localhost on our port (DNS rebinding), API calls need the session
cookie set by the launch URL, and writes need a same-origin JSON request
(CSRF). Path handling, HTML sanitising and atomic writes live in security.py.
"""
import datetime as dt
import re

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import render, scanner, security, store
from .config import (BASE, CIRCLES, CONTENT_FOLDERS, EDITABLE_ROOTS, WEB_DIR,
                     PORT, READABLE_ROOTS, READABLE_ROOT_FILES,
                     RAW_INLINE, RAW_DOWNLOAD, MAX_SAVE_BYTES,
                     HORIZON_DAYS, HOT_DAYS, ENERGY_DAYS, MAX_EVENTS_PER_DAY,
                     LESSONS_SHOWN, LESSONS_SERVED, UI_LANG)


class NoCacheStatic(StaticFiles):
    """Always revalidate static assets — stale JS after an upgrade is worse
    than a cheap 304 round-trip on localhost."""
    def file_response(self, *a, **kw):
        resp = super().file_response(*a, **kw)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


MD = render.make_markdown()
TOKEN = security.new_token()          # per launch; printed/opened by __main__
COOKIE = "aicowork_session"
HOSTS = security.allowed_hosts(PORT)

app = FastAPI(title="AI-Cowork Viewer", docs_url=None, redoc_url=None,
              openapi_url=None)


@app.middleware("http")
async def guard(request: Request, call_next):
    host = request.headers.get("host", "")
    if host not in HOSTS:
        return JSONResponse({"detail": "unexpected Host header"}, status_code=421)
    path = request.url.path
    needs_session = path.startswith("/api/") or path == "/raw"
    if needs_session and request.cookies.get(COOKIE) != TOKEN:
        return JSONResponse({"detail": "no session — open the URL printed at startup"},
                            status_code=401)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not security.origin_ok(request.headers.get("origin"), host):
            return JSONResponse({"detail": "cross-origin request refused"}, status_code=403)
        ctype = request.headers.get("content-type", "").split(";")[0].strip()
        if ctype != "application/json":
            return JSONResponse({"detail": "JSON only"}, status_code=415)
    resp = await call_next(request)
    for k, v in security.SECURITY_HEADERS.items():
        resp.headers.setdefault(k, v)
    return resp


def _path(rel, roots, root_files=()):
    try:
        return security.safe_path(BASE, rel, roots=roots, root_files=root_files)
    except security.PathRejected as e:
        raise HTTPException(400, f"bad path: {e}")


def _anchor_state():
    from aicowork_core.anchor import steering_drift
    try:
        state, drifted = steering_drift(BASE)
    except (OSError, ValueError):
        return {"state": "unchecked", "drifted": []}
    return {"state": state, "drifted": [d.split("#")[0] for d in drifted]}


def _month_bounds(y, m, months_before=1, months_after=1):
    """First day of month (y, m) minus `months_before`, last day of (y, m) plus `months_after`."""
    y0, m0 = y, m - months_before
    while m0 < 1:
        y0, m0 = y0 - 1, m0 + 12
    y1, m1 = y, m + months_after + 1
    while m1 > 12:
        y1, m1 = y1 + 1, m1 - 12
    return dt.date(y0, m0, 1), dt.date(y1, m1, 1) - dt.timedelta(days=1)


@app.get("/api/occurrences")
def api_occurrences(from_: str = Query("", alias="from"), to: str = ""):
    """Calendar rows for a date range (at most ~3 months): events and reminder windows."""
    a, b = scanner.parse_date(from_), scanner.parse_date(to)
    if not a or not b or b < a:
        raise HTTPException(400, "from and to must be YYYY-MM-DD, from <= to")
    if (b - a).days > 95:
        raise HTTPException(400, "at most three months per call")
    store.sync()
    return {"from": a.isoformat(), "to": b.isoformat(), "items": store.occurrences(a, b, dt.date.today())}


@app.get("/api/data")
def api_data():
    store.sync()
    today = dt.date.today()
    occ_from, occ_to = _month_bounds(today.year, today.month)
    since14 = today - dt.timedelta(days=HORIZON_DAYS)
    counts, balance, unassigned = store.counts_and_balance(CIRCLES, list(CONTENT_FOLDERS))
    events = store.events()
    horizon = today + dt.timedelta(days=HORIZON_DAYS)
    upcoming = []
    for e in events:
        d = scanner.parse_date(e["date"])
        if d and today <= d <= horizon and (e["status"] or "") not in (
                "done", "cancelled", "canceled", "postponed"):
            upcoming.append(dict(e, days_left=(d - today).days))
    reminders = store.reminders(today, HORIZON_DAYS)
    for r in reminders:
        # one "upcoming" signal (PHILOSOPHY #9): a reminder's date is its open
        # window's first day (or `until` once expired); days_left < 0 = overdue
        when = r.get("first") or r.get("until")
        left = r.get("days_left", -r.get("days_over", 0))
        if r["state"] == "expired":
            left = (scanner.parse_date(r["until"]) - today).days
        upcoming.append({"path": r["path"], "kind": "reminder", "title": r["title"],
                         "circle": r["circle"], "visibility": r["visibility"],
                         "date": when, "time": None, "status": "active", "tags": [],
                         "days_left": left, "state": r["state"],
                         "missed": r.get("missed", 0), "last": r.get("last"),
                         "mtime": r["mtime"]})   # Done sends it back: a stale page gets 409
    rank = {"overdue": 0, "expired": 0, "due": 1}
    upcoming.sort(key=lambda e: (rank.get(e.get("state"), 2), e["date"], e["time"] or ""))
    return {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "today": today.isoformat(),
        "base_name": BASE.name,        # not the absolute path: no reason to expose it
        # runtime knobs the UI needs ([dashboard] in the instance config)
        "ui": {"lang": UI_LANG, "horizon_days": HORIZON_DAYS, "hot_days": HOT_DAYS,
               "energy_days": ENERGY_DAYS,
               "max_events_per_day": MAX_EVENTS_PER_DAY,
               "lessons_shown": LESSONS_SHOWN},
        "inbox": scanner.scan_inbox(),
        "counts": {k: counts.get(k, 0)
                   for k in list(CONTENT_FOLDERS) + ["log", "note", "decision", "reminder"]},
        "upcoming": upcoming,
        "reminders": reminders,
        # the calendar's current month ±1, so the first paint needs no second request (D7)
        "occurrences": {"from": occ_from.isoformat(), "to": occ_to.isoformat(),
                        "items": store.occurrences(occ_from, occ_to, today)},
        "events": events,
        "balance": balance,
        "unassigned": unassigned,
        "results": scanner.scan_results(),
        "last_triage": scanner.last_triage(),
        "daily_log_today": (BASE / "06_logs" / "daily" / f"{today.isoformat()}.md").exists(),
        # dashboard signals (max 5 on screen; PHILOSOPHY.md principle 9)
        "q_stats": store.q_stats(since14),
        "overdue_contacts": store.overdue_contacts(today),
        "lessons": store.recent_lessons(LESSONS_SERVED),
        "lessons_total": store.lessons_total(),
        "on_this_day": store.on_this_day(today),
        "energy": store.energy_series(today - dt.timedelta(days=ENERGY_DAYS)),
        "practices": store.practices(),
        "apps": scanner.load_registry(),
        # the trust anchor, read only (the viewer runs on the host as the owner): a steering
        # file that changed since the owner anchored it is shown, never silently accepted
        "anchor": _anchor_state(),
        "relatable": [
            {"path": r["path"], "title": r["title"], "kind": r["kind"],
             "circle": r["circle"], "status": r["status"]}
            for r in store.all_items()
            if r["kind"] in ("project", "practice")
            and (r["status"] or "") not in ("done", "archived")],
    }


@app.get("/api/search")
def api_search(q: str = "", kind: str = "", circle: str = "", status: str = ""):
    store.sync()
    results = store.search(q[:200]) if q.strip() else store.all_items()
    if kind:
        results = [r for r in results if r["kind"] == kind]
    if circle:
        results = [r for r in results if r["circle"] == circle]
    if status:
        results = [r for r in results if r["status"] == status]
    return {"total": len(results), "items": results[:120]}


@app.get("/api/item")
def api_item(path: str):
    p = _path(path, READABLE_ROOTS, READABLE_ROOT_FILES)
    if not p.is_file() or p.suffix.lower() != ".md":
        raise HTTPException(404, "not a markdown file")
    raw = scanner.read_text(p)
    meta, body = scanner.parse_frontmatter(raw)
    html = MD.reset().convert(body)
    # GitHub-style task lists: python-markdown leaves the [ ]/[x] markers as
    # text — turn them into checkboxes; the client maps the Nth checkbox back
    # to the Nth marker in the raw text to toggle & save.
    html = re.sub(r"<li>\[ \]", '<li class="task"><input type="checkbox">', html)
    html = re.sub(r"<li>\[[xX]\]", '<li class="task done"><input type="checkbox" checked>', html)
    rel_root = path.replace("\\", "/").split("/")[0]
    return {
        "path": path,
        "title": scanner.md_title(body, p.stem),
        "meta": meta,
        "raw": raw,
        "html": html,
        "mtime": p.stat().st_mtime,
        "editable": rel_root in EDITABLE_ROOTS,
    }


class SavePayload(BaseModel):
    path: str
    raw: str
    mtime: float


@app.post("/api/item")
def api_save(payload: SavePayload):
    p = _path(payload.path, EDITABLE_ROOTS)
    if p.suffix.lower() != ".md":
        raise HTTPException(403, "only .md files are editable")
    if not p.is_file():
        raise HTTPException(404, "gone")
    if len(payload.raw.encode("utf-8")) > MAX_SAVE_BYTES:
        raise HTTPException(413, "file too large for the viewer editor")
    if abs(p.stat().st_mtime - payload.mtime) > 0.001:
        raise HTTPException(409, "file changed on disk — reload before saving")
    security.atomic_write(p, payload.raw)
    store.sync()
    return {"ok": True, "mtime": p.stat().st_mtime}


class DonePayload(BaseModel):
    path: str
    mtime: float
    date: str = ""


@app.post("/api/reminder/done")
def api_reminder_done(payload: DonePayload):
    """Mark a reminder done: set `last_done` (default today) and nothing else."""
    from aicowork_core import recur
    from aicowork_core.frontmatter import set_field
    p = _path(payload.path, {"10_reminders"})
    if p.suffix.lower() != ".md" or not p.is_file():
        raise HTTPException(404, "not a reminder file")
    if abs(p.stat().st_mtime - payload.mtime) > 0.001:
        raise HTTPException(409, "file changed on disk — reload before saving")
    try:
        raw = p.read_bytes().decode("utf-8")          # bytes as they are: CRLF stays CRLF
    except UnicodeDecodeError:
        raise HTTPException(400, "file is not UTF-8")
    meta, _ = scanner.parse_frontmatter(raw)
    if meta.get("type") != "reminder":
        raise HTTPException(400, "not a reminder (type: reminder)")
    today = dt.date.today()
    done = scanner.parse_date(payload.date) if payload.date else today
    if done is None or (payload.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", payload.date)):
        raise HTTPException(400, "date must be YYYY-MM-DD")
    problem = recur.check_done_date(meta, done, today)
    if problem:
        raise HTTPException(400, problem)
    # rule 9: last_done, and `missed` grows by the windows this Done skips (D6)
    rule = recur.parse_rule(meta)
    inc = recur.done_increment(rule, done)
    missed = meta.get("missed")
    missed = int(missed) if isinstance(missed, str) and missed.isdigit() else 0
    try:
        new = set_field(raw, "last_done", done.isoformat())
        if inc or "missed" in meta:
            new = set_field(new, "missed", str(missed + inc))
    except ValueError as e:
        raise HTTPException(400, str(e))
    security.atomic_write(p, new)
    store.sync()
    return {"ok": True, "last_done": done.isoformat(), "missed_added": inc, "missed": missed + inc,
            "mtime": p.stat().st_mtime}


class QuickAdd(BaseModel):
    title: str
    text: str = ""
    circle: str = ""
    related: list[str] = []


@app.post("/api/quickadd")
def api_quickadd(payload: QuickAdd):
    title = security.clean_title(payload.title) or "quick note"
    if len(payload.text) > MAX_SAVE_BYTES:
        raise HTTPException(413, "note too large")
    try:
        related = security.clean_related(payload.related)
    except security.PathRejected as e:
        raise HTTPException(400, str(e))
    slug = re.sub(r"[^\w]+", "-", title.lower()).strip("-")[:40] or "note"
    now = dt.datetime.now()
    circle = payload.circle if payload.circle in CIRCLES else ""
    rel_line = ""
    if len(related) == 1:
        rel_line = f"related: {related[0]}\n"
    elif related:
        rel_line = "related: [" + ", ".join(related) + "]\n"
    front = ("---\ntype: note\n"
             + (f"circle: {circle}\n" if circle else "")
             + rel_line
             + f"date: {now:%Y-%m-%d}\nstatus: active\n---\n")
    content = f"{front}# {title}\n\n{payload.text.strip()}\n"
    inbox = BASE / "00_inbox"
    for i in range(100):
        suffix = f"-{i}" if i else ""
        p = inbox / f"{now:%Y-%m-%d_%H%M}_{slug}{suffix}.md"
        try:
            security.exclusive_create(p, content)
            break
        except FileExistsError:
            continue
    else:
        raise HTTPException(409, "too many notes with this title this minute")
    return {"ok": True, "path": str(p.relative_to(BASE)).replace("\\", "/")}


@app.get("/raw")
def api_raw(path: str):
    """Attachments that .md files link to (images, PDFs, office files).
    Content roots only, extension allow-list, never active content."""
    p = _path(path, EDITABLE_ROOTS)
    if not p.is_file():
        raise HTTPException(404, "not found")
    ext = p.suffix.lower()
    if ext in RAW_INLINE:
        return FileResponse(p)
    if ext in RAW_DOWNLOAD:
        return FileResponse(p, filename=p.name,
                            content_disposition_type="attachment")
    raise HTTPException(403, f"{ext or 'this file type'} is not served")


_NO_SESSION = """<!doctype html><meta charset="utf-8"><title>AI-Cowork</title>
<p style="font-family:sans-serif">No session. Start the viewer with
<code>aicowork viz</code> and use the link it opens or prints.</p>"""


@app.get("/")
def index(request: Request, t: str = ""):
    if t:
        if t != TOKEN:
            return HTMLResponse(_NO_SESSION, status_code=401)
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(COOKIE, TOKEN, httponly=True, samesite="strict", path="/")
        return resp
    if request.cookies.get(COOKIE) != TOKEN:
        return HTMLResponse(_NO_SESSION, status_code=401)
    resp = FileResponse(WEB_DIR / "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


app.mount("/static", NoCacheStatic(directory=WEB_DIR), name="static")
