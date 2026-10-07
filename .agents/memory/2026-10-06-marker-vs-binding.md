# Draft decision record: a marker an agent can write is not a decision (red-team of 2026-10-06)

**Date**: 2026-10-06
**Agent**: AI-Cowork session (cloud workspace)
**Confidence**: High
**Status**: Placed — the owner put the record in `.agents/decisions/` on 2026-10-08
**Source**: the owner asked for the kernel to be attacked ("bẻ gãy kernel"); six attacks run on a test instance upgraded to rc.4; three went through (K, T, I), one crashed every command (G)
**Review-by**: 2027-01-06

## Problem

Three gates checked a **marker** that the agent (or an external sender) could write: `decided:` (one line), `visibility:` (one key), `check_tokens` (one spelling). CONTRIBUTING asks for a decision entry; `decisions/` is read-only to agents, so the record is drafted here.

## Finding

Proposed record for `decisions/2026-10-06_marker-vs-binding.md`:

- **Decision (owner)**: a gate that protects the owner never trusts a value that the agent can write. Either the value is **bound** to a record outside the agent's write reach (the trust anchor, written from the owner's terminal), or the value is **computed by code** at the gate, or the gate is **not claimed**.
- Applied (rc.4): the anchor binds every steering file (`policy.yaml`, `aicowork.yaml` security, the instruction file, `check_tokens`, `modules.lock`) and egress refuses on drift (K); `triage --apply` forces `visibility: private` on every file it moves (T); the leak gate matches after normalisation and reports what it cannot read (I); symlinks are reported, never followed (G); INDEX titles are the agent's words (Q); app targets are http(s) or loopback (C).
- **Where a trustworthy hash lives**: only in the anchor. `index.db` is a derived cache inside the agent's reach; a hash there is one more marker (owner's question, 2026-10-06).
- **Ceiling (not claimed)**: on a host where the agent runs with the owner's own profile, the anchor is within reach (SECURITY threat 10). An anchor outside the machine is a later decision, probably another project (FIXED-POINT).
- **Revisit**: 2027-01-06, or when a fourth marker-shaped gate is found.
- **Claim**: stance; the six replays are measured by the tests named in `docs/controls.md` C28–C31.

## Evidence

- Replays on 2026-10-06: K (policy rewritten in session → export succeeded, `doctor --quick` said OK), T (`triage --apply` kept a sender's `visibility: public`), I (six obfuscations of the owner's name passed the content check), G (one symlink → traceback in four commands).
- Branch `feat/reminder-rc4`, commits `fix(security): …`.

## Recommendation

**Do**: before adding any gate, ask who can write the value it checks.
**Don't**: store a hash in a cache or a file inside the folder and call it a check.

## Promotion candidate?

- [ ] `context/` — the one-line rule above fits `context/philosophy.md` ("close calls")
- [ ] `skills/`
- [x] Not yet — a `decisions/` record, placed by the owner
