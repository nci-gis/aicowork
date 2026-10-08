---
name: morning-brief
description: Write today's daily log for an AI-Cowork instance — carry over yesterday's "tomorrow's big rock", propose up to three big rocks from project deadlines, list today's events and active practices, flag what needs an eye in the coming days. Use when the owner asks for the morning brief, "plan my day", "daily log", or when a scheduled task points at 99_system/tasks/morning-brief.md.
---

# Morning brief

Work in the connected folder with the host's file tools. Read `aicowork.yaml` (language, modules). Today's date comes from the host or from `aicowork today` if a runner is available — never guess it.

## Procedure

1. If `06_logs/daily/<today>.md` already ends with the step-5 comment, or its Plan section has any item, stop and say so (running twice must not overwrite the owner's words).
2. Read the most recent earlier daily log. Take its Reflect line "Tomorrow's big rock" if filled. If no earlier log has a filled Reflect, say so plainly in a comment — do not invent a carry-over.
3. Read `04_projects/*/index.md` for dated deadlines and next actions; read `01_events/` for events dated today and in the next `dashboard.horizon_days` days (default 14); read `08_practices/` for `status: active` practices (flag any whose `until` has passed); read `10_reminders/` and compute each active reminder's state by CONVENTIONS "Reminders" (an upcoming one is shown within its `notice` days, else within the horizon); read `03_personas/` (except the owner's `me.md`) for `cadence` + `last_contact` (a contact is overdue when today − `last_contact` > the cadence days in `aicowork.yaml` `cadence`).
4. Create or fill today's log from `99_system/templates/<lang>/daily-log.md` (`<lang>` = `language.modules.templates`) (apply its module blocks as CONVENTIONS "Modules" says):
   - **Plan**: the carry-over first, then at most 3 big rocks in total. Mark what you proposed as a proposal in an HTML comment; the owner edits freely. If `7habits` is on, tag each with `#q1`–`#q4`.
   - **Today's schedule**: today's events (time, title, circle) and daily practices.
   - **Keep an eye**, in this order: **overdue** (reminders, with days over and missed; decision revisits with `revisit:` passed; expired practices and reminders; overdue contacts) → **due** (reminders due today) → **hot** (events and deadlines within `dashboard.hot_days`) → **upcoming** (events, deadlines and reminders in the horizon, nearest first, with days remaining). At most 5 lines; when more remain, one last line `+N more`. If a signal cannot be computed (e.g. personas without `cadence`), say which files lack which field.
   - Leave Capture, Insights and Reflect empty — they belong to the day.
5. End the file with an HTML comment: `<!-- Morning brief <date> · inbox: <n> untriaged · events in horizon: <n> · reminders due/overdue: <n>/<n> · overdue contacts: <n or "not computable"> -->`.
6. Commit `log: daily <date> (morning brief)` if the folder has git.

## Rules

- Read-only everywhere except `06_logs/daily/<today>.md` (and `INDEX.md` never).
- At most 3 big rocks; at most 5 signals mentioned in Keep an eye headings (PHILOSOPHY #9).
- Family/friend/health items are about presence, never KPIs (PHILOSOPHY #8).

## Acceptance

Conformance case L3-BRIEF: exactly one file `06_logs/daily/<today>.md` was created or filled; it has valid `type: log` frontmatter with today's `date`; its Plan has ≤ 3 items; its Reflect section is empty; Keep an eye lists every reminder that is due, overdue or expired, in the order overdue → due → hot → upcoming, at most 5 lines plus `+N more`, and the step-5 comment counts them; no other file changed except that one (and a commit); running the skill a second time changes nothing.
