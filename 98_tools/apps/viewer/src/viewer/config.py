# -*- coding: utf-8 -*-
"""The viewer's locations and knobs, on top of the shared library (`aicowork_core.config`,
`aicowork_core.contract`): the base folder, the instance settings and the folder
contract are defined there once; only what the web app alone needs lives here."""
import os
from pathlib import Path

from aicowork_core.config import *            # noqa: F401,F403  BASE, SETTINGS, HOST, PORT, URL, ...
from aicowork_core.contract import *          # noqa: F401,F403  CIRCLES, folders, SKIP_NAMES
from aicowork_core.contract import EDITABLE_ROOTS

_PKG = Path(__file__).resolve().parent          # .../98_tools/apps/viewer/src/viewer
VIEWER_DIR = _PKG.parent.parent                 # .../98_tools/apps/viewer
# derived cache; safe to delete. AICOWORK_DATA lets tests (and a second
# instance on the same machine) keep their own cache.
DATA_DIR = Path(os.environ.get("AICOWORK_DATA") or VIEWER_DIR / "data")
DB_PATH = DATA_DIR / "index.db"
WEB_DIR = _PKG / "web"


# read-only in the viewer: the kernel docs, and the catalog at the root
READABLE_ROOTS = EDITABLE_ROOTS | {"99_system", "hosts"}
READABLE_ROOT_FILES = ("INDEX.md",)
# /raw serves attachments that notes link to — never html/svg/js (same-origin XSS)
RAW_INLINE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
RAW_DOWNLOAD = {".txt", ".csv", ".md", ".pptx", ".docx", ".xlsx", ".ics",
                ".eml", ".msg", ".zip"}
MAX_SAVE_BYTES = 1_000_000
