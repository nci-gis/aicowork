---
name: weekly-review
description: "Prepare the weekly review for an AI-Cowork instance — create 06_logs/weekly/YYYY-Www.md, pre-fill the Numbers block from the week's daily logs and collect the week's #lesson lines, leaving every judgment section to the owner. Use when the owner asks for the weekly review, 'review my week', or a scheduled task points at 99_system/tasks/weekly-review.md."
---

# Weekly review (prepare, don't judge)

Work in the connected folder with the host's file tools. Read `aicowork.yaml` (language, modules). The ISO week comes from the host or `aicowork today --week`.

## Procedure

1. If `06_logs/weekly/<YYYY-Www>.md` exists and any judgment section (Wins, Stuck, Circle balance, Roles & goals) is filled, only refresh the Numbers block. Never overwrite the owner's words.
2. Read the week's `06_logs/daily/*.md` (Monday–Sunday). Count: daily logs present /7, Reflects with at least one filled line /7, average `energy` (only filled values), `#q` tags by quadrant if `7habits` is on.
3. Count untriaged inbox items and overdue contacts (as in the morning brief), reminders done this week (`last_done` in the week), reminders overdue now, and reminders **missed this week**: for each active reminder, its `missed` now minus its `missed` at the week's first commit (`git show <sha>:10_reminders/<slug>.md`; a reminder created in the week counts from 0) — `aicowork reminders --week` prints all three when a runner is available. Without git, write "not computable", never a guess (CONVENTIONS "Reminders" rule 9).
4. Create or update the file from `99_system/templates/<lang>/weekly-review.md` (`<lang>` = `language.modules.templates`; apply its module blocks as CONVENTIONS "Modules" says); fill **only** the Numbers block and the Lessons list (copy each `#lesson` line of the week, one line each, with its date).
5. At the end, add one question for the owner in an HTML comment — a real question drawn from the week's data (e.g. "Three Reflects were empty after long meeting days — what made those days different?"). One question, not a summary.
6. Commit `log: weekly <YYYY-Www> (pre-filled)` if the folder has git.

## Rules

- The review is the owner's thinking. The agent counts and asks; it does not grade the week.
- Read-only everywhere except `06_logs/weekly/<YYYY-Www>.md`.

## Acceptance

Conformance case L3-WEEKLY: one weekly file exists for the week with valid `type: log` frontmatter; its Numbers block matches the counts computed from the daily logs; the judgment sections are unchanged (empty if they were empty); no other file changed.
