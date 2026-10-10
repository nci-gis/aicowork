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
- [ ] 7. G4: rebuild an instance from `99_system/` alone with an agent ("rebuild AI-Cowork following 99_system/REBUILD.md"), conformance run on the result, the outcome recorded. Counts as the first restore drill (backlog, due 2026-11).
- [ ] 8. `docs/dpia-lite.md` turned into a template; inventory of CONVENTIONS vs. the files shipped re-checked.

Part 3 — ship (owner, `docs/publishing.md` steps 0–4)

- [ ] 9. Findings of 5–8 fixed (rc.7 if any needs a build), then version `0.0.1`, `devkit package`, REVIEW read, signed tag, zips + sha256 published.

## Do

- 2026-10-09: the owner's clone was re-pointed at the public repository (its private history, rc.3 and earlier, shares no commit with it and is retired). A stray Outlook metadata stream (`…eml:OECustomProperty`, from a copy through Windows) sat untracked in the inbox fixtures and failed the `99_system` manifest and `test_init_fresh_instance_conforms`; moved out, `verify` PASS (core 126, aicowork 100, viewer 81, devkit 24).
- 2026-10-09: steps 1 and 3 done; step 2 drafted on branch `chore/round-001`.

## Check

- [ ] `aicowork verify` PASS on the branch before each PR.
- [ ] CI: the workflow's first run on a PR passes with `--locked`; every SHA matches the tag the owner verified.
- [ ] G5: the tester's question log exists and each line has a disposition (fixed / test / accepted).
- [ ] G4: conformance on the rebuilt instance reports 0 errors, or each error is named with its cause.
- [ ] G6: each verified row carries the date and the host version.

Record what could **not** be verified as explicitly as what could.

## Act

**Learnings**:

- A file copied through Windows can carry an NTFS alternate data stream into WSL as `name:Stream`; the manifest catches it, which is the point of the manifest.

**Promotions**:

- [ ] → context/ : none yet
- [ ] → skills/ : none yet
