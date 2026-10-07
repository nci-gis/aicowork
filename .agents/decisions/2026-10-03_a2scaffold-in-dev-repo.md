---
type: decision
date: 2026-10-03
status: decided
claim: tested
tags: [aicowork, agents, harness, dev-repo]
source: owner, 2026-10-03
---

# a2scaffold in the development repository; not in instances

## Decision (owner)

The development repository adopts `a2scaffold` 0.2.1 with `--adopt`. Instances do not: the earlier "no" for the owner's instance stands.

An instance already has one memory system (`#lesson` and the daily log) and one home for skills (`99_system/skills/`). A second `.agents/` there would give the same things two homes.

## How it is applied

- The tool is pinned and run through `npx a2scaffold@0.2.1`. It is never a dependency, and nothing that ships needs Node.
- `.agents/AGENTS.md` is the heart. `CLAUDE.md`, `AGENTS.md` and `.github/copilot-instructions.md` are stubs. Copilot cannot import, so its stub restates the essentials.
- Canon lives in `.agents/context/`:
  - `project.md` holds the former root instructions;
  - `fixed-point.md` was moved from `.agents/FIXED-POINT.md` (moved back the same day, see the addendum);
  - `philosophy.md` keeps the scaffold's five principles, which already applied here, and adds this repository's four.
- The scaffold's `plan.decisions` stays off, because `.agents/decisions/` already existed with its own format.
- `.claude/settings.json` asks before an edit under:
  - `.agents/` (except `memory/`), including `decisions/` and `releases/`;
  - `99_system/`;
  - `hosts/`;
  - `.githooks/`.

  This is a speed bump in Claude Code only, not a wall.

- `.agents/memory/` is where agents write, so it is the likeliest place for a real name to appear. `devkit leakscan` scans it on every commit and push. This repository will be public, and its history goes with it.
- `devkit fmt` (Prettier) and `a2scaffold sync` agree. After formatting, `sync --dry-run` reports "Everything up to date".

## Found on the way

`a2scaffold skill validate` scored `weekly-review` 81/100: its description was 24 words long and had no trigger. The cause was a real bug. The unquoted description contained ` #lesson`, and YAML reads ` #` as the start of a comment, so every skill host saw the description cut at "collect the week's".

- Fixed: the description is now quoted, and the skill scores 100/100.
- Guarded: a new L1-KERNEL rule refuses an unquoted ` #` in a skill description, with a test. Instances built from rc.2 before this fix fail the rule until they upgrade, which is intended.

## Revisit when

- a2scaffold changes the layout of `.agents/` (check `sync --dry-run` before bumping the version); or
- a second contributor finds the stubs confusing.

**The leak gate worked on the scaffold's own text.** The generated `philosophy.md` named the framework of the tool's author. That name is one of the owner's project names, so the first commit was refused by `devkit leakscan` in pre-commit. The sentence was replaced with a neutral pointer. `sync` leaves seeded files alone, so the name does not come back.

## Addendum, same day (owner): the fixed point stays on top

`FIXED-POINT.md` went back to `.agents/FIXED-POINT.md`. It is in upper case, in English only, and above `context/`, not one canon file among several. It is the main philosophy of the repository: every session reads it first, and only the owner changes it. `.claude/settings.json` asks before any edit to it.
