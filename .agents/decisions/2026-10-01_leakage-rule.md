---
type: decision
date: 2026-10-01
status: decided
revisit: 2026-11-01
claim: measured
tags: [aicowork, egress, release, leak-gate, compliance, kernel]
source: owner, checkpoint 1 in session 2026-10-01; implemented and retested the same day
---

# The leakage rule: a leak is reported and stops; a person ships

## Decision (owner, 2026-10-01)

1. We do not wait for the employer's IT department to confirm that data needs protecting: the policy already classifies what may leave, and the tools enforce it now.
2. **Every ship decision is a person's.** The tools build, check, record and refuse; they never publish.
3. The tools guarantee one thing above all: **no leakage that is unreported, unstopped or silently bypassed.** A gate has no skip switch. An override exists only where the owner names the file on the command line, and that name is written into the receipt.
4. The kernel and the parts beside it (`hosts/`, release documents) are the permitted set. Each release is rebuilt and retested to **prove** it, not to assume it — that is what the repeated drills and gate runs are for.

## What was built (same day) and how it was retested

| Gap (checkpoint 1)                        | Change                                                                                                                                                                                                                                                                               | Retest                                                                                                                                                                                                                                                                       |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leak gate knew 4 words                    | deny-list built from the instance: `check_tokens` + owner/org (me.md) + persona file names and titles + project slugs and parts; fixture and module names excluded as fiction; `allow_tokens:` for false positives; tags listed in the review file as "names the gate does not know" | the planted text that passed at checkpoint 1 (a persona name, a team name, a drive path) is now **caught**. An organisation name, a web domain and a colleague's login that live only in prose still pass → the owner adds them to `check_tokens` (the review file prompts). |
| `package` built from a drifted/dirty tree | preflight: ring manifests must verify, tree committed, owner file present; no `--no-check` any more                                                                                                                                                                                  | planted edit, uncommitted → refused with the reason; committed + manifested → built, then **caught by the gate** and quarantined                                                                                                                                             |
| failed artifact left publishable          | moved to `_scratch/release/refused/`; `REVIEW-<v>-<date>.md` always written; clean builds logged in `06_logs/release/`                                                                                                                                                               | verified                                                                                                                                                                                                                                                                     |
| export trusted the label                  | frontmatter reduced to 7 keys, private blocks stripped, content scanned (deny-list without project names + generic patterns); hit → refuse; `--allow <path>` → recorded in the receipt; `personal-simple` export limited to `work` by default                                        | test: a public note with a persona name and an e-mail is refused; allowed by name → receipt carries the hit                                                                                                                                                                  |
| no notion of "must not be in the folder"  | `compliance.prohibited_markers` (schema, validator); `reach`/`doctor`/`conform` report, triage and export refuse; the owner's instance lists its employer's classification stamps (not quoted here — the gate would flag this very file, and did)                                    | test: a stamped inbox file → L2-COMPLIANCE error, doctor error, export refused                                                                                                                                                                                               |
| agent copies invisible                    | instruction file: copying content out of the folder is egress — only on the owner's request in the session, only what the step needs, said out loud                                                                                                                                  | prose; no machine check possible                                                                                                                                                                                                                                             |
| `upgrade` trusted the source              | `--expect-sha256`; refuses local ring drift and downgrades; upgrades hooks/launchers; prints `UPGRADING.md` instance actions; bumps `kernel_version`                                                                                                                                 | test: wrong sha, local edit, downgrade each refused with a reason                                                                                                                                                                                                            |

127 tests, `verify` PASS, kernel 11,857 of 12,000 words (budget nearly full — next change needs a cut or a decision).

## Not changed

Backups are still plaintext bundles on the same disk: the owner puts the backup folder on an encrypted volume (BitLocker/EFS) — no code can do that. The tools licence is still pending.

## Revisit when

First public tag; or a gate reports something it should not, or misses something it should have caught (each miss becomes a test).

## Addendum 2026-10-01 — what the proof is for (owner)

We do not hope the system behaves; we prove the mechanism **for an aware owner and an aware agent**: an owner who decided the policy, an agent that read the kernel. A deliberate owner is out of scope (and said so in "Not claimed"). The kernel is the soul; the tools are conveniences the owner may skip — so every guarantee must hold on the files-only path too.
First evidence on that path: the L3-REDTEAM report of 2026-10-01 (owner's instance) — 30 injected inbox items, files-only agent, no tools: nothing deleted, nothing protected touched, nothing raised, 30/30 named. One run; repeat in a host and with another model.
~~Proposed kernel wording~~ — withdrawn 2026-10-01: the owner keeps this out of the kernel; it lives in `.agents/FIXED-POINT.md` as the fixed point the kernel is built from. (Was: PHILOSOPHY "The kernel", ~45 words:) _"**Who it holds for.** The kernel's guarantees are proven for an aware owner (one who decided `policy.yaml`) and an aware agent (one that read the kernel). Against an owner who sets out to leak their own data it claims nothing."_
