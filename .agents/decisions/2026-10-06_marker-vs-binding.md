---
type: decision
date: 2026-10-06
status: decided
claim: stance
tags: [aicowork, security, egress, trust-anchor, red-team, rc.4]
source: owner, 2026-10-06, after the red-team of a test instance ("bẻ gãy kernel"); drafted by the agent in `.agents/memory/2026-10-06-marker-vs-binding.md`, placed by the owner 2026-10-08
---

# A marker an agent can write is not a decision

## Decision (owner)

A gate that protects the owner never trusts a value that the agent can write. One of three holds:

1. the value is **bound** to a record outside the agent's write reach (the trust anchor, written from the owner's terminal);
2. the value is **computed by code** at the gate;
3. the gate is **not claimed**.

**Where a trustworthy hash lives**: only in the anchor. `index.db` is a derived cache inside the agent's reach; a hash there is one more marker (owner's question, 2026-10-06).

**Ceiling, not claimed**: on a host where the agent runs with the owner's own profile, the anchor is within reach (SECURITY threat 10; `hosts/claude-code.md`). The kernel is tamper-evident there, not tamper-proof. An anchor outside the machine is a later decision, probably another project.

## Why

Six attacks were run on a test instance upgraded to rc.4; three went through and one crashed every command. The three that went through had one root: the gate checked a **marker** that the agent or an external sender could write — `decided:` (one line), `visibility:` (one key), `check_tokens` (one spelling).

- **K**: a policy rewritten in an agent session still exported; `doctor --quick` said OK.
- **T**: `triage --apply` kept a sender's own `visibility: public`.
- **I**: six obfuscations of the owner's name (confusable, zero-width, soft break, percent, entity, base64) passed the content check.
- **G**: one symbolic link gave a traceback in `reach`, `doctor`, `conform` and `export`.

## Applied (rc.4)

- The anchor binds every steering file — `policy.yaml`, the `security` block of `aicowork.yaml`, the instruction file, `check_tokens`, `modules.lock` — and `export` and `backup` refuse on drift or without an anchor; `--allow` does not bypass it; `decide` anchors by itself (K).
- `triage --apply` forces `visibility: private` on every file it moves (T).
- The leak gate matches after normalisation and reports what it cannot read, with file and line (I).
- Symbolic links are reported, never followed (G).
- INDEX titles are the agent's own words, checked (Q); app targets are http(s) or loopback (C).

Owner action, in UPGRADING: run `aicowork anchor` on the host once after upgrading, and after editing a steering file on purpose.

## Claim

Stance. The six replays are measured by the tests named in `docs/controls.md` C28–C31.

## Rule of thumb

Before adding any gate, ask who can write the value it checks. Never store a hash in a cache or a file inside the folder and call it a check.

## Revisit when

- 2027-01-06;
- a fourth marker-shaped gate is found.
