# aicowork — the command line

_Standard library only (plus the shared library `aicowork_core` beside it); the Python version is the one in `98_tools/pyproject.toml`. Run it with the launcher at the top of the folder (`aicowork <command>`), or with nothing installed: `PYTHONPATH=98_tools/apps/aicowork/src python -m aicowork <command>`._

Every command belongs to one of three groups (`aicowork --help` shows them, and a test keeps this list complete).

**Start & safety** — set up, decide, check, copy out, upgrade

| Command                           | Does                                                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `aicowork init <folder>`          | creates a new instance from the kernel (and copies these tools), with egress switched off until you decide `policy.yaml`              |
| `aicowork decide`                 | you decide `policy.yaml`: shows what it allows, and writes `decided:` when you type today's date — your terminal only, never an agent |
| `aicowork doctor`                 | health check: policy valid, kernel unchanged, inbox count, reminders due, backups, what the assistant can reach                       |
| `aicowork conform`                | runs the conformance suite (what "working correctly" means)                                                                           |
| `aicowork audit --since <commit>` | after an assistant session: what changed, and was any rule broken                                                                     |
| `aicowork reach`                  | what the connected folder exposes to the assistant, against your policy                                                               |
| `aicowork backup` / `export`      | the only ways a copy leaves the folder — both read `policy.yaml`, both leave a receipt, export is content-checked                     |
| `aicowork verify-receipts`        | checks the hash chain of those receipts                                                                                               |
| `aicowork upgrade <release.zip>`  | installs a newer kernel; refuses a wrong file, a downgrade, or overwriting your own edits                                             |
| `aicowork anchor`                 | records the kernel's hashes outside the folder — on your own computer, never from an agent session                                    |
| `aicowork manifest` / `verify`    | kernel, host pages and tools unchanged; `verify` is the gate hooks call (conformance, manifests, receipts, tests)                     |
| `aicowork denylist`               | prints every name the leak gate refuses for this instance, as one `check_tokens:` line (carry it into a new instance)                 |
| `aicowork modules`                | checks (or `--lock`s) the modules enabled in `aicowork.yaml`                                                                          |

**Every day** — capture, triage, notes, the viewer

| Command                      | Does                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| `aicowork inbox "note"`      | drops a raw text note into `00_inbox/`                                                |
| `aicowork ingest` / `triage` | quarantines untrusted inbox text; checks (or `--apply`s) a triage move plan           |
| `aicowork new` / `today`     | a note from a template in your language; today's date, weekday and ISO week           |
| `aicowork viz` / `shortcut`  | starts the viewer app (`../viewer/`, needs `uv`); a Desktop shortcut for it (Windows) |

**Advanced & evidence** — sealed copies, retention, InfoSec, host skills

| Command                        | Does                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------------------- |
| `aicowork unseal`              | opens a sealed export file with your passphrase (`below: encrypt`)                        |
| `aicowork retention` / `purge` | files whose `expires` / `review_by` is due; human-only erasure with a hash-only tombstone |
| `aicowork audit-pack` / `sbom` | an evidence folder for an InfoSec review; the tools' software bill of materials           |
| `aicowork skills`              | builds account-level skill stubs for a host that needs them                               |

Encrypted export (`below: encrypt`) needs the optional `cryptography` package (`pip install cryptography`, or run through `uv`).

## Inside

`src/aicowork/`:

| Package     | Holds                                                                                                     |
| ----------- | --------------------------------------------------------------------------------------------------------- |
| `commands/` | one module per command group (`daily`, `check`, `egress`, `instance`); each registers its own subcommands |
| `conform/`  | conformance checks L1/L2, the L3 audit runner, the evidence pack                                          |
| `egress/`   | the egress gate (policy, backup, export with content scan, receipts) and sealing                          |
| `inbox/`    | untrusted-content quarantine (`ingest`), plan-then-apply triage                                           |
| `instance/` | init, doctor, reach, new notes, folder READMEs, the trust anchor, `upgrade`                               |
| `cli.py`    | the entry point: builds the parser from the command groups                                                |

Everything shared with other tools (base folder, settings, folder contract, frontmatter, safe paths, YAML subset, manifests, leak scanners) is in `../../libs/core/` (`aicowork_core`). Building releases is not here: it is the kernel developer's devkit (`90_devkit/`), which never ships.

Tests: `pytest tests` (needs only `pytest`).
