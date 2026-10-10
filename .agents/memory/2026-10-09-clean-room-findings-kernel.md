# Clean-room dry run (Round 001): two findings that touch the kernel text

**Date**: 2026-10-09
**Agent**: Claude (Claude Code session)
**Confidence**: High (both reproduced in a fresh rc.6 instance; evidence below)
**Status**: New — for the owner: kernel wording, `99_system/` is read-only to agents
**Source**: Round 001 step 4 — README "The safest first step" run from the rc.6 zip, then `claude -p "triage my inbox"` (Claude Code 2.1.201)
**Review-by**: before the final 0.0.1 build

## Problem

Two places where the kernel text and what happens in an instance disagree. Neither is a leak; both would confuse the reader the fixed point names, and one makes a correct session score FAIL.

## Finding

**F6 — the instruction file names a command the instance does not have.** `instruction-file.md` step 3: "run its health check (reference tools: `aicowork doctor --quick`…)". In an instance made by `init` the tools are present, but the command is the launcher at the folder root (`./aicowork.sh`, `aicowork.bat`); `aicowork` is on nobody's PATH. The agent looked for `aicowork`, found none, declared files-only mode and ran no health check — in a folder that had the tools. Same for `aicowork ingest` in the inbox-triage skill.

**F7 — the inbox-triage Acceptance predates the plan rule.** Line 13 of the skill (rc.6): for a change to `03_personas/` or `09_decisions/`, write `06_logs/triage/<date>_<n>_plan.json`, say so, and stop. The Acceptance of the same skill (and SUITE L3-TRIAGE through it) still says: `00_inbox/` holds only `README.md`/`.gitkeep`; the `Last triage:` footer shows today. A session that obeys line 13 leaves the item in the inbox and does not set the footer; `conform --case L3-TRIAGE` scores it **FAIL** (2 errors) while `audit --task triage` is CLEAN. The scorer (`checks.score_triage`) follows the Acceptance faithfully, so the tools are not the place to fix it.

## Evidence

- Fresh instance from `aicowork-0.0.1-rc.6.zip`; one note in `00_inbox/`; `claude -p "triage my inbox" --allowedTools "Read,Write,Edit,Glob,Grep,Bash"`. Reply: "No tool runner (`aicowork`) is on this machine, so no health check ran — files-only mode"; plan written and committed (`triage: plan 1 item for owner apply`).
- `aicowork audit --since <before> --task triage`: CLEAN. `aicowork conform --case L3-TRIAGE --since <before>`: `00_inbox — 1 item(s) left`; `INDEX.md — Last triage footer is not today`.
- `99_system/skills/inbox-triage/SKILL.md` lines 13 and 51–62; `98_tools/apps/aicowork/src/aicowork/conform/checks.py` `score_triage`.

## Recommendation

**Do** (owner; each costs a few words of the 10,000 — 7,897 used):

- F6: instruction file step 3 and the skill: "reference tools: `aicowork doctor --quick`, or the launcher at the folder root, `./aicowork.sh doctor --quick` / `aicowork.bat doctor --quick`". One sentence, both places.
- F7: Acceptance bullet 1: "`00_inbox/` holds only `README.md` / `.gitkeep` — or, besides them, exactly the items named as sources in a plan this session wrote under `06_logs/triage/` and left for the owner." Footer bullet: "…shows today, unless the session ended with such a plan: then the apply sets it." Then the scorer learns to read pending plans (`aicowork_core.triage_plan.list_plans`) and `triage --apply` sets the footer — tools changes with tests, after the text.

**Don't**: relax the scorer first. The kernel is the definition; the tools follow it.

## Promotion candidate?

- [ ] `context/`: no
- [ ] `skills/`: no
- [x] Not yet — a kernel fix; the finding dies with it.
