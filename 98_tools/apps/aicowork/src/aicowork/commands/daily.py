# -*- coding: utf-8 -*-
"""Everyday commands for the owner and the agent: capture, triage, notes, dates, the viewer."""
import datetime as dt  # noqa: F401
import json  # noqa: F401
import sys  # noqa: F401
from pathlib import Path  # noqa: F401

from aicowork_core.config import BASE, URL  # noqa: F401
from aicowork.commands._shared import _base, _print_findings, _with_kernel  # noqa: F401


def cmd_viz(args):
    """The viewer is a separate app (98_tools/apps/viewer, needs FastAPI): run it
    in the tools' environment (98_tools/.venv, through uv). The CLI never imports it."""
    import importlib.util
    import os
    import shutil
    import subprocess
    from aicowork_core.config import release_root
    extra = ["--no-browser"] if args.no_browser else []
    env = dict(os.environ, AICOWORK_BASE=str(BASE))
    if importlib.util.find_spec("viewer") is not None:          # already in the viewer's environment
        return subprocess.call([sys.executable, "-m", "viewer", *extra], env=env)
    root = release_root()
    proj = root / "98_tools" if root and (root / "98_tools" / "apps" / "viewer").is_dir() else None
    if proj and proj.is_dir() and shutil.which("uv"):
        # the launcher installs the command line only; the viewer's packages come on first use
        return subprocess.call(["uv", "run", "--locked", "--project", str(proj), "--package", "aicowork-viewer",
                                "python", "-m", "viewer", *extra],
                               env=dict(env, UV_LINK_MODE="copy"))
    print("the viewer needs uv (https://docs.astral.sh/uv/) and 98_tools/apps/viewer/ — every other command works without it")
    return 1


def cmd_inbox(args):
    from aicowork_core.fsafe import exclusive_create
    text = " ".join(args.text).strip()
    if not text:
        print('Nothing to add. Usage: aicowork inbox "your note here"')
        return 1
    body = text + "\n"
    for raw in (args.path or []):
        # a trailing backslash before the closing quote on Windows swallows the
        # quote into the value ("d:\dir\" -> d:\dir") — clean that up
        raw = raw.strip().strip('"').strip()
        if not raw:
            continue
        if not Path(raw).expanduser().exists():
            print(f"warning: context path not found right now: {raw}")
        body += f"\n[context-path]: {raw}"
    if args.path:
        body += "\n"
    inbox = BASE / "00_inbox"
    inbox.mkdir(exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")[:-3]
    f = inbox / f"{ts}_inbox.txt"
    exclusive_create(f, body)
    extra = f" (+{len(args.path)} context path(s))" if args.path else ""
    print(f'Dropped into {f.relative_to(BASE)}{extra} — say "triage my inbox" '
          "in an agent session to file it.")
    return 0


def cmd_shortcut(args):
    if sys.platform != "win32":
        print("This command creates a Windows desktop shortcut — run it on Windows.")
        return 1
    import subprocess
    bat, name = BASE / "aicowork.bat", "AI-Cowork Viz.lnk"
    if "'" in str(BASE):
        print("error: the base path contains a quote; create the shortcut by hand")
        return 1
    ps = ("$ws = New-Object -ComObject WScript.Shell; "
          "$desktop = [Environment]::GetFolderPath('Desktop'); "
          f"$lnk = $ws.CreateShortcut(\"$desktop\\{name}\"); "
          f"$lnk.TargetPath = '{bat}'; $lnk.Arguments = '--viz'; "
          f"$lnk.WorkingDirectory = '{BASE}'; "
          f"$lnk.Description = 'AI-Cowork dashboard ({URL})'; $lnk.Save(); "
          f"Write-Output \"created: $desktop\\{name}\"")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip())
    return r.returncode


def cmd_ingest(args):
    from aicowork.inbox import ingest
    rows = ingest.ingest(_base(args), dry_run=args.dry_run)
    for path, status, fl in rows:
        print(f"  {path}: {status}" + (f"  ⚠ suspicious: {', '.join(fl)}" if fl else ""))
    print(f"ingest: {len(rows)} item(s){' (dry run)' if args.dry_run else ''}"
          + ("; tell the owner about the flagged phrases" if any(r[2] for r in rows) else ""))
    return 0


def cmd_triage(args):
    from aicowork.inbox import triage
    base = _base(args)
    try:
        moves, report = triage.apply(base, args.plan, do_apply=args.apply)
    except triage.PlanError as e:
        print(f"plan refused: {e}")
        return 1
    for s, d in moves:
        print(f"  {s.relative_to(base).as_posix()} -> {d.relative_to(base).as_posix()}")
    print(f"{len(moves)} move(s) " + (f"applied; report {report.relative_to(base)}" if report
                                       else "checked (dry run — add --apply to execute)"))
    return 0


def cmd_new(args):
    from aicowork.instance import ops
    try:
        d = dt.date.fromisoformat(args.date) if args.date else None
        p = ops.new(_base(args), args.template, slug=args.slug, date=d, lang=args.lang, title=args.title)
    except (ValueError, FileNotFoundError, FileExistsError) as e:
        print(f"new failed: {e}")
        return 1
    print(p.relative_to(_base(args)).as_posix())
    return 0


def cmd_today(args):
    from aicowork.instance import ops
    d = dt.date.today()
    if args.week:
        print(ops.iso_week(d))
    else:
        print(f"{d.isoformat()} {d.strftime('%A')} {ops.iso_week(d)}")
    return 0


def cmd_reminders(args):
    """Every active reminder with its state; --week adds the weekly review's numbers
    (done this week, overdue now, missed this week from git — E4)."""
    import json as _json
    from aicowork.instance import ops
    from aicowork_core import common as C
    base = _base(args)
    cfg, _ = C.load_yaml(base / "aicowork.yaml")
    week = args.week or ops.iso_week(dt.date.today())
    res = ops.reminder_week(base, week, cfg=cfg if isinstance(cfg, dict) else None)
    if args.json:
        print(_json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    for r in res["rows"]:
        extra = f"  missed this week: {r['missed_this_week']}" if args.week and r["missed_this_week"] is not None else ""
        print(f"  {r['state']:<9} {r['path']}  last_done: {r['last_done'] or '-'}  missed: {r['missed']}{extra}")
    if not res["rows"]:
        print("  no active reminders")
    if args.week:
        m = res["missed"] if res["missed"] is not None else "not computable (no git)"
        print(f"{week}: reminders done {res['done']} · overdue now {res['overdue']} · missed this week {m}")
    return 0


def cmd_app(args):
    """Start a registered service app (aicowork.yaml `apps`, kind: service, `command`)
    from the owner's terminal: the process runs with cwd = the instance until Ctrl-C.
    An agent session never starts one (decision kernel-host-viewer-and-apps)."""
    import os
    import subprocess
    from aicowork_core import common as C
    from aicowork_core.anchor import foreign_profile
    base = _base(args)
    cfg, err = C.load_yaml(base / "aicowork.yaml")
    apps = [a for a in ((cfg or {}).get("apps") or []) if isinstance(a, dict)] if not err else []
    if args.list or not args.id:
        for a in apps:
            run = " ".join(a["command"]) if isinstance(a.get("command"), list) else "-"
            print(f"  {a.get('id'):<16} {a.get('kind'):<9} {a.get('target')}  {run}")
        if not apps:
            print("  no apps registered (aicowork.yaml: apps)")
        return 0
    app = next((a for a in apps if a.get("id") == args.id), None)
    if app is None:
        print(f"app: no app {args.id!r} in aicowork.yaml", file=sys.stderr)
        return 2
    if app.get("kind") != "service" or not isinstance(app.get("command"), list) or not app["command"]:
        print(f"app: {args.id} is not a service with a command — open its target instead: {app.get('target')}", file=sys.stderr)
        return 2
    if os.environ.get("AICOWORK_AGENT"):
        print("app: an agent session never starts an app — the owner runs `aicowork app` in their own terminal", file=sys.stderr)
        return 2
    reason = foreign_profile(base)
    if reason and not args.here:
        print(f"app: refused — {reason}; run it from the owner's terminal on the host (or pass --here if this IS that host)", file=sys.stderr)
        return 2
    print(f"app {args.id}: {' '.join(app['command'])}  (cwd = {base}; target {app.get('target')}; Ctrl-C stops it)")
    try:
        return subprocess.call([str(x) for x in app["command"]], cwd=str(base))
    except FileNotFoundError as e:
        print(f"app: cannot start — {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


def register(add):
    p = add("viz", cmd_viz, f"start the local viewer at {URL}", base=False)
    p.add_argument("--no-browser", action="store_true")
    p = add("inbox", cmd_inbox, "drop a raw text note into 00_inbox/", base=False)
    p.add_argument("text", nargs="+")
    p.add_argument("--path", "-p", action="append", metavar="DIR", help="a directory to consult during triage")
    add("shortcut", cmd_shortcut, "create a Desktop shortcut that starts the viewer (Windows)", base=False)

    p = add("ingest", cmd_ingest, "quarantine untrusted inbox text (markers, invisible chars, flags)")
    p.add_argument("--dry-run", action="store_true")
    p = add("triage", cmd_triage, "check (or --apply) a JSON move plan")
    p.add_argument("plan")
    p.add_argument("--apply", action="store_true")
    p = add("new", cmd_new, "create a note from a template in the instance language")
    p.add_argument("template")
    p.add_argument("--slug")
    p.add_argument("--date")
    p.add_argument("--lang", choices=["en", "vi"])
    p.add_argument("--title")
    p = add("today", cmd_today, "today's date, weekday, ISO week", base=False)
    p.add_argument("--week", action="store_true")
    p = add("app", cmd_app, "start a registered service app from your terminal (aicowork.yaml apps: kind service, command)")
    p.add_argument("id", nargs="?")
    p.add_argument("--list", action="store_true")
    p.add_argument("--here", action="store_true", help="this IS the owner's host (overrides the foreign-profile check)")
    p = add("reminders", cmd_reminders, "every active reminder and its state; --week: the weekly review's numbers")
    p.add_argument("--week", metavar="YYYY-Www", nargs="?", const="", help="ISO week (default: this week)")
    p.add_argument("--json", action="store_true")
