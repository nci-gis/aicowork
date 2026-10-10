# Security — AI-Cowork 0.0.1

_Threat model, controls, limits, and what we do not claim. Evidence for every control: `docs/controls.md`; one-command evidence bundle: `aicowork audit-pack`._

## What AI-Cowork is, security-wise

A folder of plain Markdown files that an AI agent reads and writes inside a host (an agent app or IDE), plus optional local tools: a stdlib-only CLI and a loopback-only viewer. The kernel is a specification; it cannot see or control the host. So the design rule is **detect and prove**: the kernel states what the host must enforce, prevents what it owns (paths, egress, never-delete), and leaves a plain-text trail that is checked after every session.

## Threat model

One page in `docs/threat-model.md`: the assets, the actors (an external sender of mail or documents is the main threat), the seven trust boundaries, and the ten top threats with the controls against each and what each control still leaves open. The numbered threats below and in `docs/controls.md` refer to it.

## Operating rules that carry the security

- Inbox triage and anything touching untrusted content: **manual approval**, no web browsing in the same session, only needed connectors.
- After such a session, host-side: `aicowork audit --since <commit>`.
- Keep material that must not reach any model **outside** the connected folder.
- Keep the folder on a plain local disk, not a sync client.

## What we do NOT claim

- "Prompt-injection proof" or "secure against injection". Claim: mitigated by layered controls, tested on 30 red-team fixtures (flagging) and scored after real sessions (L3-REDTEAM).
- "No data leaves the machine" — the agent host sends what it reads to its model provider. The `aicowork` commands make no network calls (tested); with `uv`, the launcher installs the locked packages once, which may download them (and a Python). The model call is the named egress.
- Compliance or certification of any kind (ISO 27001/42001, SOC 2, APPI, PDP, employer policy). Claim: evidence mapped to controls.
- That folder-level permission or hook files bind any host.
- OS-level sandboxing — the kernel builds none.
- Tamper-proof logs; right-to-erasure while git history and old backups persist.
- That the leak gate catches every obfuscation. Claim: it undoes the layers listed in CONVENTIONS "Session rules" 5 (look-alike and invisible characters, soft breaks, percent, entity and base64 encodings — `fixtures/leak/`, L2-LEAK-NORM), reports hidden characters it cannot read (L2-HIDDEN), and nothing more.
- Any protection of the policy or the instruction file before the owner has run `aicowork anchor` on their own computer — and, on a host where the agent runs with the owner's own profile, the anchor itself is within the agent's reach (threat 10: tamper-evident, not tamper-proof).
- SLSA levels or reproducible builds (not yet verified).
- That a leak already pushed can be undone by the tools. A force-push removes the commits from the branch, but the hosting service keeps unreachable commits fetchable by hash until it purges them (on request, or in time); and whoever fetched meanwhile has them. The scans exist to refuse the push — before it, not after.

## Reporting a vulnerability

Until the public repository exists, report privately to the maintainer named in the release notes. Please include the version (`99_system/VERSION`), the component (kernel / tools / a host page) and a reproduction. Do not open public issues for undisclosed vulnerabilities.

## Leakage rule

Every gate in the tools follows one rule: **a leak is reported and stops the operation; nothing is skipped silently and no flag turns a gate off.** `package` has no skip switch and quarantines a failed artifact; `export` refuses on a content hit unless the owner names the file, and the name is written into the receipt; `upgrade` refuses on a wrong hash, local drift or a downgrade unless the owner says so on the command line. The ship decision — tagging, publishing — is a person's, every time; the tools build, check and record.
