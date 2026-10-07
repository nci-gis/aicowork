# aicowork_core — the shared library

_Standard library only (Python: see `98_tools/pyproject.toml`). Every tool in `98_tools/` and the devkit build on it; it builds on nothing._

| Module        | Holds                                                                                                                                                                         |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `config`      | where the base folder is; the instance settings from `aicowork.yaml` (runtime knobs warn, security knobs refuse)                                                              |
| `contract`    | the folder contract in code: circles, folder map, editable roots, skipped names                                                                                               |
| `frontmatter` | the frontmatter subset every tool parses the same way                                                                                                                         |
| `recur`       | reminders: when a repeating duty is upcoming, due, overdue or expired (CONVENTIONS "Reminders")                                                                               |
| `fsafe`       | safe relative paths, atomic writes, create-without-overwrite                                                                                                                  |
| `yamlite`     | the YAML subset of CONVENTIONS "Instance config"                                                                                                                              |
| `anchor`      | the trust anchor, read side: where it lives, whether this profile is the owner's, the steering-file hashes and their drift                                                    |
| `manifest`    | ring manifests, trust anchor                                                                                                                                                  |
| `scan`        | the leak scanners (owner names after normalisation, generic patterns), the hidden-character report, release file selection — one implementation for export and release builds |
| `common`      | shared helpers: git, hashes, versions, the deny-list                                                                                                                          |

Tests: `pytest tests`. Rule: this library imports nothing from any tool.
