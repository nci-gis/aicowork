# 99_system — the kernel

_A note for humans (README files are never content). The six documents below are what the kernel's 10,000-word budget counts._

This folder **is** AI-Cowork: a specification of how a folder of plain files, an AI agent and its owner work together. It contains no personal data and no code. Copy it into an empty folder, follow `REBUILD.md`, and any competent agent on any host can build a working instance — that is the acceptance test, and `conformance/` makes it checkable.

## Read in this order

| File                   | Answers                                              |
| ---------------------- | ---------------------------------------------------- |
| `PHILOSOPHY.md`        | **Why** — the principles, and what the kernel is     |
| `CONVENTIONS.md`       | **What** — folders, frontmatter, rules, rings        |
| `REBUILD.md`           | **How** — from an empty folder to a working instance |
| `conformance/SUITE.md` | what "a proper AI-Cowork" means, case by case        |
| `host-contract.md`     | the four things any agent host must provide          |
| `instruction-file.md`  | the text every agent session reads first             |

Also here: `schemas/`, `templates/<lang>/`, `skills/`, `tasks/`, `modules/`, `presets/`, `aicowork.example.yaml`, `VERSION`. Host adapters (not kernel) live in `hosts/`.

## Starting a new instance

- **With the reference tools**: `aicowork init <folder> --preset corporate-strict|personal-simple --lang en|vi`, then fill `03_personas/me.md`, decide `policy.yaml` once, copy `INSTRUCTIONS.md` (written by `init` from `instruction-file.md`) into your host's instruction file, and run `aicowork doctor`.
- **Without tools**: follow `REBUILD.md` by hand or ask an agent to; check with any conformance runner.

## Upgrading this folder

`aicowork upgrade <aicowork-kernel-X.zip>` shows the diff, takes a git bundle, archives removed files to `07_archive/`, and never touches your instance files.

## Changing the kernel

Change the right layer: **why** → PHILOSOPHY (rare, deliberate); **what** → CONVENTIONS + its conformance case; **how** → REBUILD. Every rule change gets a decision entry. Stay under the word budget. Then `aicowork manifest --write` so drift detection knows the change was intended.
