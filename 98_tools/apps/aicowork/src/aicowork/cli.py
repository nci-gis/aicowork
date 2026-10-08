# -*- coding: utf-8 -*-
"""AI-Cowork CLI — the reference implementation's single entry point.

Called by the root launchers (aicowork.bat / aicowork.sh), or directly inside a
host sandbox with no installs:  PYTHONPATH=98_tools/apps/aicowork/src python3 -m aicowork <cmd>
(the shared library beside it, 98_tools/libs/core, is found automatically)
Standard library only. `viz` starts the separate viewer tool.

Commands live in `aicowork.commands.<group>`; each group registers its own
subcommands. Release building is not here: it is the kernel developer's
`devkit` (90_devkit/), which never ships.
"""
import argparse
import importlib
import sys

from aicowork_core.config import BASE

# Every command belongs to exactly one group, so its purpose is stated where it is
# added (tested). Nothing here is optional to keep or to drop: it is how --help reads.
GROUPS_OF_COMMANDS = {
    "start & safety — set up, decide, check, copy out, upgrade": [
        "init", "decide", "doctor", "conform", "audit", "reach", "backup", "export",
        "verify-receipts", "upgrade", "anchor", "manifest", "verify", "denylist", "modules"],
    "every day — capture, triage, notes, the viewer": [
        "inbox", "ingest", "triage", "new", "today", "reminders", "viz", "shortcut"],
    "advanced & evidence — sealed copies, retention, InfoSec, host skills": [
        "unseal", "retention", "purge", "audit-pack", "sbom", "skills"],
}

EPILOG = """\
daily use:
  1. drop anything into 00_inbox/     (or: aicowork inbox "your note")
  2. in an agent session say:         "triage my inbox"
  3. afterwards, host-side:           aicowork audit --since <commit>
  aicowork doctor                      health of this instance
  aicowork viz                         dashboard, search, calendar, live edit

commands by purpose:
""" + "".join(f"  {title}:\n    {', '.join(names)}\n" for title, names in GROUPS_OF_COMMANDS.items()) + """
base folder: """ + str(BASE)

ALIASES = {"--viz": "viz", "-v": "viz", "--inbox": "inbox", "-i": "inbox",
           "--input": "inbox", "--shortcut": "shortcut",
           "lint": "conform"}


def build_parser():
    from aicowork.commands import GROUPS
    parser = argparse.ArgumentParser(
        prog="aicowork", description="AI-Cowork reference tools — kernel checks, audit, egress, viewer.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd")

    def add(name, fn, help, base=True):
        p = sub.add_parser(name, help=help)
        p.set_defaults(fn=fn)
        if base:
            p.add_argument("--base", metavar="DIR", help="instance folder (default: this one)")
        return p

    for group in GROUPS:
        importlib.import_module(f"aicowork.commands.{group}").register(add)
    return parser


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ALIASES:
        argv[0] = ALIASES[argv[0]]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "fn", None):
        parser.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
