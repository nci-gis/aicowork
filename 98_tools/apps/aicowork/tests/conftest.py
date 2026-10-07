# -*- coding: utf-8 -*-
"""Test fixtures. aicowork_core.config resolves BASE at import time, so a
throwaway base folder is created and pointed at *before* anything is imported.
The real instance and its index.db are never touched."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 98_tools/apps/aicowork
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[1] / "libs" / "core" / "src"))

_TMP = Path(tempfile.mkdtemp(prefix="aicowork-test-"))
BASE = _TMP / "base"
for d in ("00_inbox", "01_events", "02_emails", "03_personas", "04_projects",
          "05_results", "06_logs/daily", "06_logs/weekly", "07_archive",
          "08_practices", "09_decisions", "99_system/skills/x"):
    (BASE / d).mkdir(parents=True, exist_ok=True)
(BASE / "INDEX.md").write_text("# INDEX\n\n---\nLast triage: 2026-01-01\n", encoding="utf-8")
(BASE / "99_system" / "PHILOSOPHY.md").write_text("# Philosophy\n", encoding="utf-8")
(BASE / "99_system" / "skills" / "x" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
(BASE / "01_events" / "2026-01-01_hello.md").write_text(
    "---\ntype: event\ncircle: work\ndate: 2026-01-01\nvisibility: private   # comment\n---\n"
    "# Hello\n\nsearchable <script>alert(1)</script> needle <img src=x onerror=alert(2)>\n",
    encoding="utf-8")
(BASE / "01_events" / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")
(BASE / "01_events" / "page.html").write_text("<script>alert(1)</script>", encoding="utf-8")
(BASE / "01_events" / "img.svg").write_text("<svg onload=alert(1)/>", encoding="utf-8")
# a sibling folder whose name starts with the base name — the classic
# string-prefix bypass of `str(p).startswith(str(BASE))`
SIBLING = _TMP / "base_evil"
SIBLING.mkdir()
(SIBLING / "secret.md").write_text("# secret\n", encoding="utf-8")

os.environ["AICOWORK_BASE"] = str(BASE)
os.environ["AICOWORK_DATA"] = str(_TMP / "data")
