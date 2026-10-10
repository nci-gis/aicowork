# Round 001: Close 0.0.1 — the gates, not features

**Status**: In Progress
**Part of**: [v0.0.1-plan.md](../v0.0.1-plan.md), release-candidate track R3–R6
**Date started**: 2026-10-09
**Date completed**: —

## Goal

0.0.1 has one job: prove reliability and safety for a reader who knows nothing about AI (FIXED-POINT). rc.4–rc.6 added what the owner's first use asked for; the release track itself has not moved past R4 since 2026-10-03. This round runs the open gates (G4, G5, G6), fixes what they find, and leaves the owner one step from publishing. No new feature enters until then.

## Plan

Part 1 — an honest tree and plan

- [x] 1. `v0.0.1-plan.md` says where we are (rc.6, repository public, `verify` PASS); this round opened.
- [ ] 2. CI from `docs/ci/verify.yml.template`: `uses:` pinned to commit SHAs; the owner verifies each SHA before the workflow is enabled.
- [x] 3. The two decision drafts in `memory/` are placed (`decisions/` holds them since 2026-10-08) — nothing left to do.

Part 2 — the gates

- [ ] 4. G5 preparation (agent): the five README steps run on a clean Linux user from the rc.6 zips; a one-page tester sheet and a question-log template written for the non-expert tester.
- [ ] 5. G5 (owner + a non-expert tester, second machine, zips alone): every question written down; each becomes a doc fix or a test.
- [ ] 6. G6: `hosts/claude-code.md` H4 (scheduled prompt) verified on a date; `hosts/github-copilot.md` H3 when a Copilot session is available.
- [x] 7. G4: rebuild an instance from `99_system/` alone with an agent ("rebuild AI-Cowork following 99_system/REBUILD.md"), conformance run on the result, the outcome recorded (2026-10-09: `memory/2026-10-09-rebuild-drill-g4.md`; 0 questions, L1 pass, L2 one error explained, 12 text items for the owner). Counts as the first restore drill (backlog, due 2026-11).
- [x] 8. `docs/dpia-lite.md` turned into a template (2026-10-09: §0 inputs, generic §4, the one owner's jurisdictions kept as an example); inventory re-checked — REBUILD §3 omits `README.md`, `LICENSE`, `MANIFEST.sha256` (F9, kernel wording, for the owner).

Part 3 — ship (owner, `docs/publishing.md` steps 0–4)

- [ ] 9. Findings of 5–8 fixed (rc.7 if any needs a build), then version `0.0.1`, `devkit package`, REVIEW read, signed tag, zips + sha256 published.

## Do

- 2026-10-09: the owner's clone was re-pointed at the public repository (its private history, rc.3 and earlier, shares no commit with it and is retired). A stray Outlook metadata stream (`…eml:OECustomProperty`, from a copy through Windows) sat untracked in the inbox fixtures and failed the `99_system` manifest and `test_init_fresh_instance_conforms`; moved out, `verify` PASS (core 126, aicowork 100, viewer 81, devkit 24).
- 2026-10-09: steps 1 and 3 done; step 2 drafted on branch `chore/round-001` (PR #8). CI's first run: `verify` and `leakscan` passed, `sbom --out dist/…` tracebacked (no `dist/`) — fixed in the tool with a test.
- 2026-10-09, step 4 (G5 dry run, Linux, no sudo so a fresh `HOME` and a bare `PATH` stood in for a new user; rc.6 zips built from `origin/dev`, leak gate clean): steps 1, 2, 4 pass; `doctor: OK — 0 errors`. With `/usr/bin/python3` = 3.10 only, the launcher refused plainly (correct). Steps 3 and 5 with Claude Code 2.1.201, non-interactive: triage followed the skill, stopped with a plan (rc.6 rule), `audit` CLEAN, `triage --apply` moved the item. Findings:
  - F1 README step 2 and `init`'s "next" list say `aicowork init` / `aicowork doctor`; the shipped command is `./aicowork.sh` / `aicowork.bat`. **Fixed** (README, `init` text, test).
  - F2 Python-only path with an old Python: clear refusal. No change.
  - F3 README step 4 says `{{…}}`; `me.md` has `<…>` and empty `Name:` / `Org:`. **Fixed** (README).
  - F4 `init` already commits, then asks for a commit. **Fixed** (`init` text: "commit what you changed").
  - F5 the tester's first commit fails without a git identity. **Fixed** (`init` text gives the two lines).
  - F6 the agent did not run `doctor --quick`: it looked for `aicowork` on PATH, not for the launcher at the root. **Kernel wording** (instruction file step 3) — for the owner, `memory/2026-10-09-clean-room-findings-kernel.md`.
  - F7 L3-TRIAGE scores a session that ended with a plan as FAIL (item left, footer not today): the skill's Acceptance predates the rc.6 plan rule in the same skill; the scorer follows the Acceptance. **Kernel wording** — same memory file.
  - F8 `triage --apply` leaves the moves uncommitted and says nothing about it; `doctor` then reports uncommitted changes. Open: say "commit when you are done" in its output, or commit as `triage: apply <plan>`? (owner)
  - A `-p` session needs `--allowedTools` on the command line (host page H4).
- 2026-10-09, step 6 (G6): `hosts/claude-code.md` H1, H3 verified, H4's mechanism verified, spike items 1 and 3 dated. Copilot H3 still `?`.
- 2026-10-09, step 4 deliverable: `docs/clean-room-test.md` (tester sheet + question log).

## Check

- [x] `aicowork verify` PASS on the branch before each PR (2026-10-09: core 128, aicowork 103, viewer 81, devkit 24).
- [ ] CI: the workflow's first run on a PR passes with `--locked` (2026-10-09: green from the second push on); every SHA matches the tag the owner verified — **owner**.
- [ ] G5: the tester's question log exists and each line has a disposition (fixed / test / accepted). The agent's dry run is not the gate: a non-expert on a second machine is.
- [x] G4: conformance on the rebuilt instance reports 0 errors, or each error is named with its cause (1 error, L2-OWNER, cause: the kernel's reserved name in `check_tokens`; `memory/2026-10-09-rebuild-drill-g4.md`).
- [x] G6: each verified row carries the date and the host version (Claude Code 2.1.201, 2026-10-09). Copilot: not verified.

Record what could **not** be verified as explicitly as what could.

## Act

**Learnings**:

- A file copied through Windows can carry an NTFS alternate data stream into WSL as `name:Stream`; the manifest catches it, which is the point of the manifest.

**Promotions**:

- [ ] → context/ : none yet
- [ ] → skills/ : none yet
