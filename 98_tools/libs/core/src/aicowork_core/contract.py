# -*- coding: utf-8 -*-
"""The kernel's folder contract, as code. CONVENTIONS.md is the source of truth;
every note's frontmatter is written against these names, so they are defined
here only and never read from a config file (renaming a circle would silently
orphan the `circle:` field in every file)."""

CIRCLES = ["work", "family", "friend", "health"]
CONTENT_FOLDERS = {                              # kinds in the circle-balance chart
    "event": "01_events",
    "email": "02_emails",
    "persona": "03_personas",
    "project": "04_projects",
    # Practices are the life circles' primary content type (PHILOSOPHY #8: life is
    # measured by consistency & presence). Leaving them out made family/friend/health
    # structurally near-empty on the chart. Decisions/logs/archive stay out: meta, not presence.
    "practice": "08_practices",
}
# Reminders are duties measured by done/overdue, not presence (#8): counting them
# in the balance chart would skew it toward admin, so they stay out of it.
EXTRA_FOLDERS = {"log": "06_logs", "note": "07_archive",
                 "decision": "09_decisions", "reminder": "10_reminders"}
ALL_FOLDERS = {**CONTENT_FOLDERS, **EXTRA_FOLDERS}
EDITABLE_ROOTS = {"00_inbox", "01_events", "02_emails", "03_personas",
                  "04_projects", "05_results", "06_logs", "07_archive",
                  "08_practices", "09_decisions", "10_reminders"}
SKIP_NAMES = {".gitkeep", "README.md", "readme.md"}
# where `upgrade` archives the kernel files a release removed: retired kernel text,
# not notes — never exported, and not judged as notes (CONVENTIONS "Folders")
ARCHIVED_KERNEL = "07_archive/kernel-"


def is_archived_kernel(rel):
    return str(rel).replace("\\", "/").startswith(ARCHIVED_KERNEL)
