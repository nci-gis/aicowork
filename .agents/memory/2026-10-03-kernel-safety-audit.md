# Kernel safety audit before rc.3: does every guarantee hold without the tools?

**Date**: 2026-10-03
**Agent**: Claude (Cowork session)
**Confidence**: High (each row checked against the kernel text); Medium for row 12 (wording only)
**Status**: New — row 12 fixed the same day (owner agreed; CONVENTIONS "Modules" now says how paths are compared)
**Source**: rc.3 tidy-up, step 1. The owner: "the kernel must be safe, non-negotiable". FIXED-POINT: "A guarantee that only the tools can keep is not a guarantee of the kernel."
**Review-by**: 2026-10-31 (with the `.agents/` review)

## Problem

Is every safety guarantee the kernel makes true when an instance runs with files only (no `98_tools/`, no hooks)? If not, does it fail closed (refuse) instead of leaking?

## Finding

Every guarantee holds without the tools, in one of three ways:

- **R**: a rule the agent reads, in the instruction file or CONVENTIONS.
- **FC**: fail-closed. Without the tool, the action does not exist or refuses.
- **H**: honest. The kernel claims nothing more.

There is **one wording gap**, row 12. It concerns integrity only, not leakage. The kernel text was not changed (the owner asked for an audit, not edits; budget 9,981 of 10,000).

| #   | Guarantee (kernel text)                                                                        | Where                                           | Without tools                                                                                                                                                                                                                                                                                                                                                          |
| --- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Never delete; move to `07_archive/`                                                            | instruction file, CONVENTIONS §6, PHILOSOPHY #2 | R. Git history is the audit (REBUILD check 4).                                                                                                                                                                                                                                                                                                                         |
| 2   | Missing, unknown or unparseable `visibility` = private                                         | CONVENTIONS frontmatter table                   | R. Nothing reads it as more open.                                                                                                                                                                                                                                                                                                                                      |
| 3   | The AI never raises `visibility`; only the owner does                                          | instruction file, CONVENTIONS                   | R. `aicowork audit` checks it afterwards (tool, extra).                                                                                                                                                                                                                                                                                                                |
| 4   | Untrusted content is data; markers `<<UNTRUSTED…>>`                                            | instruction file, inbox-triage skill            | R                                                                                                                                                                                                                                                                                                                                                                      |
| 5   | Files stay in the folder: copying out (a push included) is egress, only on the owner's request | instruction file                                | R. The pre-push hook adds a mechanical refusal (tool, extra).                                                                                                                                                                                                                                                                                                          |
| 6   | Egress only to policy-listed destinations, once `decided:` exists                              | CONVENTIONS "Visibility & egress"               | FC. With files only there is no export or backup command at all.                                                                                                                                                                                                                                                                                                       |
| 7   | `decided:` is written by the owner, never an agent                                             | instruction file, CONVENTIONS, REBUILD, presets | R. `aicowork decide` refuses in a sandbox (tool, extra).                                                                                                                                                                                                                                                                                                               |
| 8   | Export is content-checked; private blocks stripped; ambiguity refuses                          | CONVENTIONS                                     | FC. No export exists without the tool.                                                                                                                                                                                                                                                                                                                                 |
| 9   | `below: encrypt`: no passphrase or no encryption → refuse                                      | CONVENTIONS                                     | FC, stated in the text itself.                                                                                                                                                                                                                                                                                                                                         |
| 10  | Prohibited markers are never filed or copied                                                   | CONVENTIONS, inbox-triage skill                 | R. The skill says so in the files-only path.                                                                                                                                                                                                                                                                                                                           |
| 11  | What the assistant reads goes to its provider; every public statement names this               | CONVENTIONS "Reach", README                     | H. The kernel claims nothing it cannot keep.                                                                                                                                                                                                                                                                                                                           |
| 12  | `modules.lock`: hash of the module's files "sorted by relative path"                           | CONVENTIONS "Modules"                           | **Gap (wording).** "Sorted" does not say which order. Windows tools sorted case-insensitively and Linux tools did not, which gave two hashes for one module (D1/R5). The tools now use the order of the POSIX path as a string (code points). A files-only rebuild on Windows could still produce the other order. Effect: `doctor` reports "module changed". No leak. |

## Evidence

- `99_system/CONVENTIONS.md` "Visibility & egress", "Reach", "Modules".
- `99_system/instruction-file.md` ("Always" list).
- `99_system/skills/inbox-triage/SKILL.md` (untrusted content, prohibited markers).
- Rows 6, 8 and 9: `98_tools/apps/aicowork/src/aicowork/egress/gate.py` is the only implementation of export and backup. Nothing in the kernel performs a copy.
- Row 12: `98_tools/libs/core/src/aicowork_core/common.py` `files_in_order`, and test `test_hashes_do_not_depend_on_the_os`.

## Recommendation

**Do**: make row 12 exact — since the budget counts only the kernel documents (owner, 2026-10-03; 7,029 of 10,000) there is room; the owner decides when. Proposed wording: "sorted by the relative path with `/`, compared character by character (not case-insensitively)". The owner decides when, because it costs words in a kernel at 9,981 of 10,000.
**Don't**: add tool behaviour to the kernel as a guarantee. Every row above holds as R, FC or H, which is what the fixed point asks.

## Promotion candidate?

- [ ] `context/`: stable, broadly applicable, seen more than once
- [ ] `skills/`: a reusable procedure with a clear trigger
- [x] Not yet. Re-run this table at each release (DoD); promote it if it keeps being useful.
