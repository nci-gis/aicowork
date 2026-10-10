# Promotion Log

> Append-only log of memory entries promoted to `context/` or `skills/`.
> See [PDCA.md](PDCA.md) for methodology and [AGENTS.md](../AGENTS.md) for promotion criteria.

---

<!-- Append new entries below this line using the format:

## YYYY-MM-DD: [Topic] → [Destination]

**Source**: memory/[filename]
**Rationale**: [1-2 sentences]
**Promoted by**: [Human name]

-->

## 2026-10-03: Initial canon at adoption → context/

**Source**: no memory entry. Seeded when a2scaffold 0.2.1 was adopted. `project.md` holds the rules the root instruction files had before. `fixed-point.md` was moved from `.agents/FIXED-POINT.md`. Principles 6–9 in `philosophy.md` come from the kernel's decisions.
**Rationale**: the owner decided to adopt a2scaffold in the development repository on 2026-10-03 (`decisions/2026-10-03_a2scaffold-in-dev-repo.md`). Canon that already existed was moved into it, not rewritten.
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-03: The fixed point → `.agents/FIXED-POINT.md`

**Source**: owner, in session (no memory entry)
**Rationale**: the fixed point is the main philosophy of the repository, so it sits above `context/`. Every session reads it first. It is now English only, and the Vietnamese duplicate was removed so there is one text to keep true.
**Promoted by**: the owner

## 2026-10-03: Ambiguity fails closed; fixes from the review of rc.2 → kernel, tools, `decisions/`

**Source**: owner, in session (no memory entry). The review of `0.0.1-rc.2` found seven issues, and the owner set the ambiguity stance in the same session.
**Rationale**: the agent changed areas that are read-only to agents, on the owner's explicit instruction ("go ahead"):

- `99_system/`: a CONVENTIONS rule, the SUITE cases L2-AMBIGUITY and L1-ROOT, `conformance/ambiguity.json`, fixtures, an example `modules.lock`, and "No export leaves silently";
- `.agents/decisions/2026-10-03_ambiguity-fails-closed.md`.

The kernel stays within its budget (9,921 of 10,000 words).
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-03: Second review of the rc.3 work and the first real use of rc.2 → kernel, tools, hosts, `decisions/` (branch `dev`)

**Source**: owner, in session (no memory entry). Findings M1–M8 (second review), F1–F10 and D1–D4 (first run), P (where the Python version lives); the owner accepted the agent's proposals for O1–O5 and P-A…P-H and asked for one commit per kind of finding on a `dev` branch.
**Rationale**: the agent changed areas that are read-only to agents, on the owner's explicit instruction:

- `99_system/`: the instruction-file rule that an agent never writes `decided:` (also CONVENTIONS, REBUILD, both presets); REBUILD's exact `.gitignore`/`.gitattributes`; AMB-PB-NEAR covers an unclosed marker (`ambiguity.json` and its fixture); the example instance's `modules.lock`;
- `.githooks/`: scan after the manifests are added, refuse untracked ring files, the receiving remote only, no version number;
- `hosts/claude-cowork.md`: `uv` behind the proxy, scheduled tasks;
- `.agents/decisions/2026-10-03_ambiguity-fails-closed.md`: addenda 1–3 (trailer false alarm, the Python floor written once, the unclosed marker).

The kernel stays within its budget (9,966 of 10,000 words).
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-03: rc.3 tidy-up → `decisions/README.md`, `plan/`, `memory/`

**Source**: owner, in session ("go ahead" on the four-step tidy-up; keep every tool, keep a2scaffold).
**Rationale**: `.agents/` had grown larger than the kernel. Nothing was removed from a2scaffold. An index in `decisions/README.md` says which records hold and when each is revisited. `plan/` lists only what is open. The kernel safety audit went to `memory/`, where agents may write.
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-06: content type `reminder` (rc.4) → kernel `99_system/`, tools, devkit fixtures (branch `feat/reminder-rc4`)

**Source**: owner, in session — "implement the rc.4 reminder plan with its default decisions (D1–D5)".
**Rationale**: the agent changed `99_system/` (read-only to agents) on the owner's explicit instruction: CONVENTIONS (folder row, type list, fields `repeat`/`days`/`last_done`, section "Reminders", Work vs Life line), `schemas/frontmatter.schema.json`, `templates/en/reminder.md` and the weekly-review Numbers line, the three skills, REBUILD §1, SUITE (L1-KERNEL, L1-FRONTMATTER, L2 scopes, L3-BRIEF), the example instance (`10_reminders/renew-parking-permit.md`, `## Reminders`). The decision record is drafted in `memory/2026-10-06-reminder-type-decision-draft.md` for the owner to place in `decisions/`. Kernel budget: 7,356 of 10,000 words.
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-06: red-team fixes (rc.4) → kernel `99_system/`, `SECURITY.md`, `docs/controls.md` (branch `feat/reminder-rc4`)

**Source**: owner, in session — "bẻ gãy kernel" (attack it), then "sửa plan và thực hiện" with decisions D1–D9 of `05_results/2026-10/2026-10-06_rc4-plan-2.md` (owner's instance).
**Rationale**: the agent changed `99_system/` on the owner's instruction: CONVENTIONS (inbox files leave as private; `decided:` bound to the trust anchor that now covers every steering file; token matching after normalisation; symlinks and hidden characters reported; reminders rule 9 adds `missed`), the frontmatter schema and reminder template (`missed`), SUITE rows L2-POLICY-BOUND, L2-REACH-LINK, L2-INDEX-CLEAN, L2-LEAK-NORM, L2-HIDDEN, redteam fixtures 31–32, `fixtures/leak/`, the inbox-triage skill (private on filing; INDEX titles in the agent's words). The decision record is drafted in `memory/2026-10-06-marker-vs-binding.md` for the owner to place in `decisions/`.
**Promoted by**: the owner (instruction in session), carried out by the agent

## 2026-10-09: Round 001 opened; `v0.0.1-plan.md` brought to rc.6; CI workflow drafted → `plan/`, `.github/workflows/`

**Source**: owner, in session ("go ahead, and proceed by order as suggested") on the agent's plan to close 0.0.1 through its open gates G4, G5, G6.
**Rationale**: `plan/` and `.github/` are read-only to agents beyond `Do`/`Check` of an active round. The owner authorised: `cycles/Round_001.md` opened, `v0.0.1-plan.md` "Where we are" and row R4 brought from rc.2 to rc.6, and `docs/ci/verify.yml.template` turned into a workflow with `uses:` pinned to commit SHAs that the owner verifies before enabling.
**Promoted by**: the owner (instruction in session), carried out by the agent
