# -*- coding: utf-8 -*-
"""Entry point: `aicowork viz` or `python -m viewer`."""
import sys
import threading
import webbrowser

import uvicorn

from .config import (BASE, HOST, PORT, URL, SETTINGS_PATH, SETTINGS_WARNINGS,
                     SECURITY_ERRORS)
from . import store


def main():
    # The viewer has no user accounts (PHILOSOPHY not-do list: auth), so it
    # must never listen beyond this machine, and it must not run on a config
    # it could not read. Refuse rather than warn.
    if SECURITY_ERRORS:
        for e in SECURITY_ERRORS:
            print(f"error: {e}")
        print("the viewer did not start (security settings fail closed)")
        return 2
    from .api import app, TOKEN
    if not (BASE / "00_inbox").is_dir():
        print(f"warning: {BASE} does not look like an AI-Cowork base folder "
              "(set AICOWORK_BASE to override)")
    for w in SETTINGS_WARNINGS:
        print(f"warning: {w}")
    r = store.sync()
    launch = f"{URL}/?t={TOKEN}"
    try:
        from importlib.metadata import version
        ver = version("aicowork-tools")
    except Exception:
        ver = "?"
    print(f"AI-Cowork Viewer v{ver}  ->  {launch}   (Ctrl+C to stop)")
    print("  the link carries this launch's session key; it changes on every start")
    print(f"watching: {BASE}   index: {r['total']} files "
          f"({r['updated']} refreshed)")
    if SETTINGS_PATH.is_file():
        print(f"settings: {SETTINGS_PATH}")
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(launch)).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
