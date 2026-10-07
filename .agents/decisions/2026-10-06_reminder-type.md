---
type: decision
date: 2026-10-06
status: decided
claim: stance
tags: [aicowork, kernel, reminder, content-type, rc.4]
source: owner, 2026-10-06, the rc.4 implementation plan (kept in the owner's instance, derived from its own decision record of the same date); drafted by the agent in `.agents/memory/2026-10-06-reminder-type-decision-draft.md`, placed by the owner 2026-10-08
---

# Reminders — a tenth content type for dated duties that repeat

## Decision (owner)

A tenth content type, `reminder`: a dated duty that repeats ("check the account on the 15th and 16th of every month"). One file per duty in `10_reminders/<slug>.md`. Fields: `repeat` (weekly, monthly, yearly), `days`, `date`, optional `until`, `status`; the only state is `last_done` (and `missed`, a reference count, since the red-team fixes of the same release). The occurrence rules 1–9 are stated in CONVENTIONS "Reminders"; the reference implementation is `aicowork_core.recur`.

Choices fixed by the plan's defaults (D1–D5):

- an own folder, `10_reminders/`: one kind, one folder; events keep their naming pattern;
- the key is `days`, never `on` (YAML 1.1 reads `on` as true);
- reminders stay out of the circle-balance chart: duties, not presence (PHILOSOPHY #8);
- `INDEX.md` gets a `## Reminders` section, between Practices and Decisions (conformance L1-ROOT);
- kernel version 0.0.1-rc.4.

**No new dashboard signal.** Reminders join the existing "upcoming" signal (PHILOSOPHY #9).

**Out of scope**: "last weekday of the month", "every 2 weeks", a time of day, notifications outside the viewer and the morning brief, `.ics` export.

## Why

A practice is measured by presence, an event happens once; neither says "this duty is due again, and was it done". Filing recurring duties as practices or repeated events made the morning brief guess. A type whose only state is `last_done` keeps the kernel small (the rules fit in nine sentences) and lets any files-only rebuild compute the same answer as the tools.

## Claim

The type is a stance. The occurrence maths is measured by `98_tools/libs/core/tests/test_recur.py` (clamp, leap day, windows across periods, weekly weekend, `until` inclusive, expired, missed windows, years without an end, invalid rules, the `on:` trap).

## Revisit when

- two months of use have passed (about 2026-12-06);
- a rule outside rules 1–9 is asked for.
