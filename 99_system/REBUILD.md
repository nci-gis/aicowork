# REBUILD — recipe to recreate AI-Cowork from an empty folder

_How. Companion to PHILOSOPHY.md (why) and CONVENTIONS.md (what). Host-independent: nothing here assumes a particular agent app, IDE, model or tool._

**Acceptance criterion**: an agent session given **the kernel release** (`99_system/`, and `hosts/` if a host is used), the owner inputs of §0 and an empty folder rebuilds an equivalent working system **without asking the owner**, and the result passes conformance **level 2** (`99_system/conformance/`). The trinity (PHILOSOPHY, CONVENTIONS, this file) says how; **all** of `99_system/`, the trinity included, is copied verbatim, never rewritten — its `MANIFEST.sha256` must still verify. Every question the agent asks is a kernel defect — fix the kernel, not the agent's memory.
**Drill**: quarterly. Rebuild into a temp folder, run the checks in §6, and record the result (date, host, model, questions asked): a `09_decisions/` entry in the owner's own instance; if the agent cannot reach it, a file `06_logs/conformance/YYYY-MM-DD_rebuild-drill.md` in the temp folder, copied over by the owner.
_Tools are optional: the kernel works with files alone. Commands written `aicowork …` belong to the optional reference implementation (released separately); every step that names one can also be done by hand._

## 0. Inputs from the owner

A rebuild needs exactly these; everything else has a default in this file.

| Input                                                                                      | Goes to                                                                                                    |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| name, organisation, timezone, languages                                                    | identity line of `03_personas/me.md` (the timezone lives only there; "today" is the host's local date)     |
| the spellings of name and organisation that must never ship                                | `check_tokens` of `03_personas/me.md`                                                                      |
| roles (one line each, what the role owes)                                                  | "## Roles" of `03_personas/me.md`                                                                          |
| machine kind: own machine → `personal-simple`; managed by an employer → `corporate-strict` | `policy.yaml` and `aicowork.yaml` `security.preset` (same value)                                           |
| the host, if any                                                                           | the instruction file name (from `hosts/<host>.md`); no host → `INSTRUCTIONS.md` at the root                |
| languages for chat, content, templates                                                     | `aicowork.yaml` `language` (default `en`; `ui` and `modules.99_system` keep the copied value unless given) |

**Not an input**: the policy decision. `policy.yaml` is copied from the preset _undecided_ (no `decided:` line). Only the owner adds `decided: YYYY-MM-DD`, once, deliberately (PHILOSOPHY #11) — never an agent, even when asked; until then every egress command refuses. The rebuild never fills it.

## 1. Folder skeleton

```
00_inbox/  01_events/  02_emails/  03_personas/  04_projects/
05_results/  06_logs/daily/  06_logs/weekly/  06_logs/triage/  07_archive/
08_practices/  09_decisions/  10_reminders/  07_archive/00_inbox-originals/  99_system/
```

Each top-level folder `00_`–`10_` gets a `README.md`: a `# <folder>/` heading, then that folder's purpose and naming from CONVENTIONS "Folders", word for word, and the line "Rules: `99_system/CONVENTIONS.md`." — the starting point for a person or an agent opening the folder (README files are never content). Other empty folders hold a `.gitkeep` (`07_archive/00_inbox-originals/` receives the original of every triaged inbox file). `git init`. Root `.gitignore`, exactly: `Thumbs.db` `desktop.ini` `.DS_Store` `~$*` `*.tmp` `*.bak` `_scratch/` `_to_delete/` `_tmp/` `.venv/` `98_tools/apps/viewer/data/` `__pycache__/` `.pytest_cache/` `*.bundle`, plus the editor settings folders the host page lists. Never ignore a folder that holds skill pointers the host page tells you to keep. Root `.gitattributes`: `* text=auto eol=lf` (one line ending everywhere, so audits diff cleanly), then `*.bat text eol=crlf`, `*.cmd text eol=crlf` (Windows scripts need it), `*.png binary`, `*.jpg binary`, `*.pdf binary`, `*.pptx binary`, `*.zip binary`, `*.bundle binary`. Without a host page there are no editor folders to add to `.gitignore`. `00_inbox/` gets only its `.gitkeep`.

Root files:

- `INDEX.md` — live catalog: title `# INDEX — Live Catalog`, then `##` sections Events · Emails · Personas · Projects · Practices · Reminders · Decisions · Recent results (the owner's own `me.md` is not listed), then a `---` rule and the footer `Last triage: —` (a dash until the first triage).
- `aicowork.yaml` — instance config, copied from `99_system/aicowork.example.yaml` (CONVENTIONS "Instance config"); set `language` and `security.preset` from §0, keep every other key as copied (tool knobs are harmless without tools).
- `policy.yaml` — egress policy, copied verbatim from the §0 preset in `99_system/presets/` — undecided until the owner decides it (§0).
- the instruction file (name from §0), containing `99_system/instruction-file.md` verbatim, header line included.
- `hosts/` — host adapters, beside the kernel and not part of it (CONVENTIONS "Rings"); optional, hash-locked like the kernel.
- `03_personas/me.md` — the owner, copied from `99_system/templates/en/owner.md` and filled: `check_tokens` (every spelling of name, organisation and people that must never ship), the identity line, the roles (sections without a role are left out).
- `modules.lock` — for every module enabled in `aicowork.yaml`: a JSON object `{"<name>": "<sha256>"}` (CONVENTIONS "Modules").
- Nothing else at the root: the release's own files (`LICENSE`, `NOTICE.md`, `CHANGELOG.md`, `docs/`, …) describe the release and are not copied into an instance.

Finish with **one commit** `chore: init instance from kernel <VERSION>`, authored with whatever git identity the host has (the kernel sets none; if there is none, set a repository-local one that names the agent, never the owner). Registering scheduled prompts and skills is a host step (`hosts/<host>.md`); a files-only rebuild registers nothing — rituals then start by hand.

## 2. Content contract

Exactly as CONVENTIONS.md: folder table, filenames `YYYY-MM-DD_slug.md`, frontmatter keys (schema `99_system/schemas/frontmatter.schema.json`), machine-read tokens, visibility fail-closed, never-delete.

## 3. Kernel contents (`99_system/`)

| Path                                            | Is                                                                                                                                |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `PHILOSOPHY.md`, `CONVENTIONS.md`, `REBUILD.md` | the trinity                                                                                                                       |
| `VERSION`                                       | kernel version, one line                                                                                                          |
| `host-contract.md`                              | the four things any host must provide                                                                                             |
| `instruction-file.md`                           | cold-start text every session reads first                                                                                         |
| `schemas/`                                      | JSON Schemas: frontmatter, `aicowork.yaml`, `policy.yaml`, `module.yaml`                                                          |
| `templates/<lang>/`                             | one template per content type; the kernel ships `en` (other languages come as modules)                                            |
| `skills/<name>/SKILL.md`                        | procedures an agent follows, each with an **Acceptance** section: `inbox-triage`, `morning-brief`, `weekly-review`, `topic-watch` |
| `tasks/<name>.md`                               | scheduled-task specs; a host's scheduled prompt is one line pointing at one of these                                              |
| `modules/<name>/`                               | modules shipped with the kernel (`7habits`)                                                                                       |
| `presets/`                                      | `policy.yaml` presets                                                                                                             |
| `aicowork.example.yaml`                         | instance config example                                                                                                           |
| `conformance/`                                  | the suite that defines "proper"                                                                                                   |

## 4. Skills

Every skill is a Markdown procedure with Agent Skills frontmatter (`name` = folder name, lowercase-hyphen; `description` says when to use it). It names no host or tool: it speaks of "the connected folder" and "the host's file and shell tools". It ends with an **Acceptance** section — what must be true afterwards, written so a conformance case can check it.

## 5. Scheduled work

A ritual that should run on a schedule (morning brief, weekly review, topic watch) is a **task spec** in `99_system/tasks/`: what to read, what to write, whether it needs the local folder (device-bound), and why it is safe to run twice (idempotent). The host's scheduled prompt is a single line: "Read `99_system/tasks/<name>.md` in the connected folder and follow it."

## 6. Checks after a rebuild

Checks 2–3 create content and commits; run them after the initial commit (or in a throw-away copy).

1. Conformance L1 and L2 pass (with any runner, or by hand — `conformance/SUITE.md` "Running the suite by hand").
2. Drop a note into `00_inbox/` (any file from `conformance/fixtures/inbox/`), run the `inbox-triage` skill → the note lands in the right folder with valid frontmatter, INDEX.md is updated, the inbox is empty, a `triage:` commit exists.
3. Run the `morning-brief` skill → today's daily log exists, built from the template, with the plan carried over from the last Reflect (on a fresh instance there is none: the log says so).
4. Nothing was deleted (`git log --diff-filter=D` shows only moves into `07_archive/`).
5. Count the questions the agent asked. Zero passes the drill.
