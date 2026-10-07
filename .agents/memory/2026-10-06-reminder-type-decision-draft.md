# Draft decision record: content type `reminder` (kernel 0.0.1-rc.4)

**Date**: 2026-10-06
**Agent**: AI-Cowork session (cloud workspace)
**Confidence**: High
**Status**: Placed — the owner put the record in `.agents/decisions/` on 2026-10-08
**Source**: the owner's implementation plan for rc.4 (kept in the owner's instance, `05_results/`, derived from its `09_decisions/2026-10-06_reminder-type.md`); implemented on branch `feat/reminder-rc4`
**Review-by**: 2026-12-06

## Problem

CONTRIBUTING asks every kernel rule change to come with a decision entry. `decisions/` is read-only to agents, so the record is drafted here for the owner to place (or to replace with a pointer to the instance decision).

## Finding

Proposed record for `decisions/2026-10-06_reminder-type.md`:

- **Decision (owner)**: a tenth content type, `reminder` — a dated duty that repeats — in `10_reminders/<slug>.md`. Fields `repeat` (weekly/monthly/yearly), `days`, `date`, optional `until`, `status`; the only state is `last_done`. Occurrence rules 1–9 in CONVENTIONS "Reminders"; reference implementation `aicowork_core.recur`.
- **Choices fixed by the plan's defaults (D1–D5)**: own folder `10_reminders/` (one kind → one folder; events keep their naming pattern); key `days`, never `on` (YAML 1.1 reads `on` as true); reminders stay out of the circle-balance chart (duties, not presence, #8); INDEX gets `## Reminders` (L1-ROOT); kernel version 0.0.1-rc.4.
- **No new dashboard signal**: reminders join the existing "upcoming" signal (#9).
- **Out of scope**: "last weekday of the month", "every 2 weeks", time of day, notifications outside the viewer/brief, `.ics` export.
- **Revisit**: after two months of use (about 2026-12-06), or when a rule outside rules 1–9 is asked for.
- **Claim**: the type is a stance; the occurrence maths is measured by `98_tools/libs/core/tests/test_recur.py`.

## Evidence

- Commits on `feat/reminder-rc4`: core (`recur`, `set_field`), CLI, viewer, kernel text.
- Kernel budget after the change: 7,356 of 10,000 words (was 7,029 at rc.3).

## Recommendation

**Do**: copy the record above into `decisions/` and add its row to `decisions/README.md` (budget column: 7,356 used at rc.4).
**Don't**: leave the kernel change without a decision record in this repository.

## Promotion candidate?

- [ ] `context/` — stable, broadly applicable, seen more than once
- [ ] `skills/` — a reusable procedure with a clear trigger
- [x] Not yet — a `decisions/` record, placed by the owner
