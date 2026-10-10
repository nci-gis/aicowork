# Rebuild drill (gate G4): an instance from `99_system/` alone, by an agent, files only

**Date**: 2026-10-09
**Agent**: Claude (Claude Code session); the rebuild itself by a fresh sub-agent that saw only the folder
**Confidence**: High (the rebuilt folder was checked with the reference tools and diffed against `init`)
**Status**: Resolved 2026-10-09 — items 1–8, 10, 11 and the `kernel_version` check in the kernel text and devkit on the owner's instruction (promotions.md); 9 and 12 accepted as is
**Source**: Round 001 step 7. Host: Claude Code 2.1.201 (sub-agent, no tools, no network). Kernel: 0.0.1-rc.6 (`origin/dev`). Questions asked of the owner: **0**.
**Review-by**: before the final 0.0.1 build; then 2027-01 (next drill)

## Problem

Does the kernel text alone rebuild a conforming instance, and where does the text make the agent guess?

## Finding

**Result**: one commit, 23 instance files, `policy.yaml` undecided, `MANIFEST.sha256` intact, `modules.lock` equal to the fixture's (the hashing rule reads the same on both sides). Conformance L1 passes. L2 reported one error, **L2-OWNER on `CONVENTIONS.md`**, because the owner inputs used the kernel's own reserved names (`Example Co`) as `check_tokens` — not a rebuild fault; see below. Against an `init`-made instance the differences are: README layout, `.gitignore` comment lines, `00_inbox/` README vs `.gitkeep`, `06_logs/triage/` (rebuild has it, `init` did not — fixed in the tools), an INDEX subtitle line `init` writes.

**Fixed in the tools / documents (this round)**: `06_logs/triage/` in the skeleton (`init`, L1-SKELETON, fixture); README's example `check_tokens` no longer the kernel's reserved name; a plan cannot move a raw item into a content folder (`triage_plan.check_plan`).

**For the owner — kernel text** (the sub-agent's list, condensed; each quotes the sentence):

1. REBUILD §1 contradicts itself: "each top-level folder `00_`–`10_` gets a `README.md`" vs "`00_inbox/` gets only its `.gitkeep`". `init` writes the README. Say which.
2. `06_logs/` sub-folders: REBUILD §1 lists `triage/`; CONVENTIONS "Folders" names `audit/`, `egress/`, `conformance/` and not `triage/`; §6 writes to `conformance/`, which the skeleton does not create. One list.
3. `aicowork.example.yaml` says `kernel_version: 0.0.1-rc.2` while `VERSION` is rc.6; REBUILD says "keep every other key as copied". The agent set it to `VERSION` and flagged the deviation. Either `devkit fixtures` stamps the example too, or REBUILD says "set `kernel_version` to `VERSION`".
4. `me.md`: REBUILD lists `check_tokens`, the identity line and the roles as the fields to fill; the template's `date: {{YYYY-MM-DD}}` is not among them and would fail L1-FRONTMATTER. Add `date`.
5. `check_tokens`: §0 routes the owner's spellings straight in; CONVENTIONS rule 5 says list every spelling (`<First Last>`, `<FirstLast>`). Say whether the rebuild derives variants or the owner lists them.
6. Timezone format unspecified (fixture `UTC+7`, owner gave an IANA name). Say one.
7. Folder README layout: "word for word" says what to copy, not the shape. `init`'s shape could be the stated one.
8. Git identity: "whatever identity the host has" — fine for a private instance; the sentence could say that the owner's own name there is not a leak (the instance is never published).
9. SUITE L1-FRONTMATTER ("every `.md` in `01_`–`04_`, …") vs the ten mandated READMEs without frontmatter: by hand, a literal runner fails them. Exclude `README.md` in the SUITE text as the tools do.
10. `hosts/` is referenced from §0, §1, §5, CONVENTIONS and the instruction file, but a kernel-only release has no `hosts/`. Say "from the full release".
11. Whether the first commit includes `99_system/` is unsaid (the agent included it; L2-MANIFEST then has history to check).
12. Smaller: the preset's and example's "copy to the instance root as …" header comments land in the instance; the default branch name is unsaid; `circle: work` stays in `me.md` for an owner with a Family role.

**L2-OWNER and the reserved names**: the kernel uses `Example Co` as its made-up company. An owner whose `check_tokens` contain that string (the README's own example did, until this round) gets "owner-identifying token in a kernel file" on `CONVENTIONS.md`. The check is right to fire; the example was wrong. Whether the gate should treat the kernel's reserved names specially is a design question (the fixture avoids it with `Example Co.` and `ExampleCo`).

## Evidence

- Sub-agent report in the session of 2026-10-09 (Round 001 Do); rebuilt folder `g4/instance` (scratch, discarded).
- `aicowork conform --base <rebuilt> --level 2`: 1 error, L2-OWNER. `doctor`: the same plus the usual three warnings of a fresh instance.
- `diff -rq -x .git -x 99_system <init-made> <rebuilt>`: 15 lines, listed above.

## Recommendation

**Do**: the twelve items are one editing pass of REBUILD §0–§1 and two SUITE rows, before the final build (budget 7,897 of 10,000). Re-run this drill on the final kernel text; record it in the owner's `09_decisions/` as REBUILD's drill line asks.
**Don't**: make `init` match the rebuild's guesses; make the text say what `init` does, then the rebuild follows.

## Promotion candidate?

- [ ] `context/`: no
- [x] `skills/`: maybe — "run the rebuild drill" is a repeatable procedure (prepare a folder with `99_system/`, the owner inputs, the sub-agent prompt, conformance, the diff). Promote after the second drill if the steps hold.
