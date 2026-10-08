# Changelog

## 0.0.1-rc.5 — 2026-10-08 (release candidate, not for publication) — reminders complete, honest dry-runs

### The kernel

- **`notice:` on a reminder** (CONVENTIONS "Reminders" rule 8): an upcoming window is shown within `notice` days of `first` when set, else within the dashboard horizon as before. Optional, a whole number of days; the schema, the template and the example instance (`notice: 7`) carry it. Due, overdue and expired never change.
- **Keep an eye has an order** (morning brief, L3-BRIEF): overdue → due → hot (within `dashboard.hot_days`) → upcoming, nearest first; at most 5 lines, then one line `+N more`.
- **Reminders missed this week** (weekly review): `missed` stays cumulative in the file (rule 9); the week's number is the field now minus the field at the week's first commit, read from git; without git the review says "not computable", never a guess. The weekly template's Numbers line reads `Reminders done / overdue / missed`.
- Decision record `kernel-host-viewer-and-apps`: aicowork = kernel + host + viewer; everything else is an app registered by link; reading is a surface, writing is audited. Kernel documents: 7,805 of 10,000 words.

### Security

- **A dry run runs the binding gate** (`docs/controls.md` C34). `backup --dry-run` and `export --dry-run` skipped the trust-anchor check, so a drifted or unanchored policy got a would-be file name while the real run refused (found during the rc.4 upgrade test). A dry run now refuses the same way and still writes nothing. (Measured: `test_dry_run_runs_the_binding_gate`.)

### Reference tools

- `aicowork reminders`: every active reminder with its state, `last_done` and `missed`; `--week [YYYY-Www]` adds done this week, overdue now and missed this week (from git); `--json`.
- `recur`: `Rule.notice`, validated like the other fields; `state()` walks to `notice` or to the horizon.

### The repository

- The development repository is public from here on (decision `kernel-repo-split`, addendum 2026-10-08): `LICENSE` (MIT) at the repository root, carried by the full artifact too; `devkit leakscan` and the git hooks run in a contributor's clone without a private instance, with the generic patterns only (`devkit package` still needs a private instance). CONTRIBUTING says so.

## 0.0.1-rc.4 — 2026-10-06 (release candidate, not for publication) — reminders

### The kernel

- **Reminders** (Stance): a new content type for dated duties that repeat — "check the account on the 15th and 16th of every month". One file per duty in `10_reminders/<slug>.md` (`type: reminder`, `repeat` weekly/monthly/yearly, `days`, `date`, optional `until`, `status`); its only state is `last_done`. CONVENTIONS "Reminders" states nine occurrence rules — clamp, windows, range, open window, upcoming/due/overdue (with missed windows), expired, not computed, shown with the existing "upcoming" signal, Done — so any implementation computes the same answer. The key is `days`, never `on` (YAML 1.1 reads `on` as true). A practice is measured by presence, a reminder by done, an event happens once.
- Reminders stay out of the circle-balance chart: duties, not presence (PHILOSOPHY #8). No new dashboard signal (#9).
- Schema, template `reminder.md`, REBUILD §1 (`10_reminders/`, `## Reminders`), conformance (L1-KERNEL, L1-FRONTMATTER, L2 scopes `00_`–`10_`, L3-BRIEF lists the example instance's reminder). The morning brief lists due, overdue and expired reminders and upcoming ones in the horizon; triage files duties into `10_reminders/`; the weekly review counts reminders done and overdue. Kernel documents: 7,356 of 10,000 words.

### Security (red-team of 2026-10-06, asked for by the owner)

Six attacks were run against a test instance; three went through, one crashed every command. Each is now refused or reported, with a rule in the kernel and a test in the tools (`docs/controls.md` C28–C31):

- **A policy rewritten in an agent session could still export** (K). `decided:` is in force only while `policy.yaml` matches the owner's trust anchor, which now binds every file that steers the agent (the policy, the `security` block of `aicowork.yaml`, the instruction file, `check_tokens`, `modules.lock`); `export` and `backup` refuse on drift or without an anchor, `--allow` does not bypass it, `decide` anchors by itself, `doctor` and the viewer say when a steering file drifted. Owner action in UPGRADING: run `aicowork anchor`. (Measured: `test_export_refuses_policy_drift`.)
- **A sender's own `visibility: public` survived triage** (T). `triage --apply` makes every filed note private. (Measured: `test_triage_apply_forces_private`, red-team fixture 31.)
- **The owner's name hidden by look-alike or invisible characters, a soft line break, percent, entity or base64 encoding passed the content check** (I). The leak gate matches after undoing those layers (`fixtures/leak/`, L2-LEAK-NORM); hidden characters that match nothing are reported with file and line (L2-HIDDEN, `06_logs/conformance/<date>_hidden-chars.md`) and counted in the export receipt. What is not undone is listed in SECURITY "not claimed". (Measured: `test_export_refuses_every_leak_fixture_and_reports_hidden_chars`.)
- **One symbolic link crashed `reach`, `doctor`, `conform` and `export`** (G). Links are reported (L2-REACH-LINK, an error when they point outside the folder) and never followed. (Measured: `test_symlink_reported_not_followed`.)
- INDEX titles are the agent's own words, checked (L2-INDEX-CLEAN, fixture 32); app targets are http(s) or loopback. A hash in `index.db` would be one more marker inside the agent's reach — trust hashes live only in the anchor (98_tools/REBUILD.md). The ceiling on a host where the agent has the owner's profile is stated in `hosts/claude-code.md` (Stance; tamper-evident, not tamper-proof).

### Reference tools

- The occurrence rules are implemented once, in `aicowork_core.recur` (standard library, pure functions; Measured by `libs/core/tests/test_recur.py`: clamp, leap day, windows across periods, weekly weekend, until inclusive, expired, missed windows, years without an end, invalid rules, the `on:` trap).
- Conformance checks a reminder's `repeat`/`days`/`until`/`status`; a missing `10_reminders/` or `## Reminders` says it is new in this version and points here. `init` creates both; `new reminder`; triage may move into `10_reminders/`; `doctor` prints "reminders: N due, M overdue, K expired".
- Viewer: reminders join "Keep an eye" with their state (in N d, due today, overdue N d · N missed, expired) and a **Done** button. Done (`POST /api/reminder/done`) writes `last_done` — today by default, never in the future or before `date` — and adds the windows it skips to `missed` (a reference count; done late is not missed), and changes no other byte of the file (comments, order and CRLF kept; mtime guard). The cache schema is 5 and rebuilds by itself; deleting it gives the same answer.

## 0.0.1-rc.3 — 2026-10-03 (release candidate, not for publication) — fixes from two reviews of rc.2 and its first real use

### The kernel

- **Ambiguity is an error, never a guess** (CONVENTIONS "Visibility & egress"). `conformance/ambiguity.json` lists the ways a note can be read two ways — frontmatter that is not cleanly fenced or not in the YAML subset, a `visibility` key or value that only looks right, nested, orphaned or lookalike private-block markers, including a marker that lost its closing `-->` — each with a fixture. Such a note reads as private and every export refuses until a person fixes it; naming the file does not override this. New conformance cases L2-AMBIGUITY and L1-ROOT (`INDEX.md` sections, `modules.lock`).
- "Nothing leaves silently" now reads "No export leaves silently": what the assistant reads goes to its provider, without a receipt.
- **`decided:` is the owner's, always.** The instruction file, CONVENTIONS and REBUILD say that an agent never writes `decided:` in `policy.yaml`, even when asked: the owner adds it on their own computer.
- REBUILD §1 lists exactly the `.gitignore` and `.gitattributes` lines that `init` writes (Windows scripts keep CRLF).
- The 10,000-word budget counts the kernel's six documents, listed in `99_system/README.md` — PHILOSOPHY, CONVENTIONS, REBUILD, conformance SUITE, host contract, instruction file — not skills, tasks, templates or modules (owner, 2026-10-03).
- CONVENTIONS "Modules": the files of a module are sorted by their path compared character by character, not case-insensitively — the same `modules.lock` on every OS, by the text alone. PHILOSOPHY's last Vietnamese heading is now English.
- Retired kernel files that `upgrade` archives (`07_archive/kernel-<version>/`) are not notes: conformance does not judge them as notes and export never takes them. Their templates keep `{{…}}` placeholders, which L2-AMBIGUITY would otherwise refuse after every upgrade that removes one.

### Reference tools

- Viewer: the search bar and the dashboard share one centred column (at most 1,360 px wide). On a wide screen the spare room is split evenly on both sides, instead of the search bar stretching across the screen while the cards stopped at 1,000 px and left the right side empty. Below that width nothing changes, except that the cards no longer stop at 1,000 px.
- One strict parser reads every note's frontmatter (it used to be a lenient second parser that read `visibility: "public` as public and let a nested `visibility: public` override the real one). Quoted values are decoded exactly as YAML says (`\"`, `''`, `\x..`, `\u....`); an unknown escape is an error, not literal text.
- Export finds private blocks by their grammar, not by counting markers: nested blocks and a block closed before it opens refused nothing before and leaked the private tail. A marker missing its `-->` is caught too.
- A prohibited marker is checked in the whole original file, before private blocks are stripped.
- A note with Windows line endings has its frontmatter reduced on export like any other (before, every key left with it).
- `03_personas/me.md` is read exactly: no frontmatter, an empty one, or a `check_tokens` the parser cannot read makes every leak gate refuse, instead of scanning for nothing.
- The same bytes and hashes on every OS: module locks, ring manifests and release zips list files by their POSIX path (Windows sorted them differently, so the same module had two hashes), every file the tools write uses LF, and a release carries `aicowork.bat` with CRLF whatever the building machine holds.
- `aicowork decide`: the owner decides `policy.yaml` at an interactive terminal on the host, by typing today's date; it refuses inside an agent's sandbox and without a terminal.
- `upgrade --apply` records, by hash, every file it wrote (`06_logs/upgrade/<date>_<from>_to_<to>.json`); `audit` accepts exactly those files with one warning to confirm the upgrade, and still flags anything edited afterwards. Kernel text and fixtures are no longer judged as notes by audit (it flagged the release's own fixtures as "visibility raised").
- `doctor` names what is uncommitted (up to five paths); the receipt that a backup or export writes after itself is expected and reported as such.
- `upgrade` imports everything it needs before it replaces a file (rc.2's stopped halfway when upgrading itself to newer code). Upgrade from rc.2 with the rc.3 tools (UPGRADING).
- `init` writes the `## Practices` section into `INDEX.md`, writes `modules.lock`, and ends with the one commit REBUILD asks for.
- **The Python version is written once**, as `requires-python` in `98_tools/pyproject.toml` (3.11; rc.2 claimed 3.9, never tested, and `init` failed there). The entry point, the launchers and the git hooks read it through one small check and say plainly when a Python is too old; no document restates it.
- With `uv`, the launcher installs the command line only (`--package aicowork`); `aicowork viz` adds the viewer the first time it runs, and `aicowork verify` runs the tests in the whole tools environment. "No network connections" is now said of the commands, which is what the test proves: `uv` may download the locked packages, and a Python, once.
- The viewer's index no longer fails when a note has a list where a single value belongs (`date: [2026-10-03]`): that field is left empty.

### Development repository (never shipped)

- The pre-commit hook writes the ring manifests first and leak-scans the index after, so the scan reads exactly what the commit holds; it refuses while a ring has untracked files. The pre-push hook scans every blob and commit message being pushed and counts as already sent only what the receiving remote has, not what another remote has.
- One reviewed false alarm (owner, 2026-10-03): the AI assistant's no-reply address in `Co-Authored-By:` trailers, recorded by hash in `90_devkit/leak-reviewed.json`; anything else still refuses.
- A release build refuses a shipped document that claims nothing leaves without naming the model-call exception.
- `devkit fixtures --check`: the generator reproduces the committed fixtures byte for byte (tested).
- A release build refuses when VERSION, the tools' package versions and `uv.lock` disagree, or when the fixtures are not what the generator writes: a stale lock would break every user's `uv run --locked`.

### Host pages

- Claude Cowork: `uv` works behind the inspecting proxy with `system-certs = true`; a scheduled task's "succeeded" is not evidence — bind each task to the computer and judge it by the file it writes.

### Documents

- README: the first steps say plainly that, once an assistant is connected, the files it opens go to the AI service; the files-only path now includes the rebuild step that creates `INDEX.md`, `aicowork.yaml` and `policy.yaml`.

## 0.0.1-rc.2 — 2026-10-03 (release candidate, not for publication)

_Supersedes 0.0.1-rc.1 (built the same day, never installed)._
First release candidate of the first versioned release. Earlier internal version numbers are retired.

### The kernel (`99_system/`) — the specification

- What the kernel is: a specification, not software. Five-point membership test; four rings (kernel, host adapters, reference tools, instance). English only; ≤ 10,000 words of prose.
- `PHILOSOPHY.md` (12 principles, each labelled with how it is evidenced), `CONVENTIONS.md` (folders, frontmatter, visibility and egress, modules, instance config), `REBUILD.md` (build an instance from the text alone, no tools needed).
- `host-contract.md` (the four things any assistant host must provide), `instruction-file.md`, schemas, policy presets, templates, three skills (inbox triage, morning brief, weekly review), scheduled-task prompts, the `7habits` module.
- `conformance/`: what "working correctly" means, levels L1–L3, with a fictional example instance.

### Host adapters (`hosts/`)

- Claude Cowork (verified 2026-10-01) with a hardening guide for IT; Claude Code and GitHub Copilot (documented, not yet verified).

### Reference tools (`98_tools/`) — optional

- `aicowork` command, standard library only (Python ≥ 3.9): `init`, `doctor`, `conform`, `audit`, `reach`, `backup`, `export`, `unseal`, `upgrade`, `denylist`, `verify` and more (`98_tools/README.md`). A local, offline viewer (`aicowork viz`, needs `uv`).
- Nothing leaves the folder except through `backup` and `export`, both governed by `policy.yaml`, both leaving a hash-chained receipt. A fresh policy refuses every copy until its owner adds `decided:`.
- Export is content-checked (owner names, organisation, personas, e-mail addresses, keys, paths); a hit refuses unless the owner names the file, and that is recorded. `below: encrypt` seals what must not travel in clear (AES-256-GCM, key from the owner's passphrase).
- Release artifacts are built from a committed, manifest-clean tree and pass two leak scanners; a failed artifact is quarantined. The deny-list is built from the owner's own instance, never shipped.
- `upgrade` checks the published sha256, refuses to overwrite local edits or to downgrade without saying so, and prints what the owner must change by hand.
- No network connections (tested).

### Changed since the last internal build

- The kernel's development moved to its own repository, which holds no owner data. Releases are built there with the devkit; the leak gate reads the deny-list from the owner's private instance (`devkit package --deny-from`, or `git config aicowork.denyFrom`). Every commit and push of that repository is leak-scanned (`devkit leakscan`, git hooks).
- `98_tools/` layout: `libs/core/` (shared library `aicowork_core`: settings, folder contract, safe paths, leak scanners…), `apps/aicowork/` (the command line, commands grouped in `commands/`), `apps/viewer/`; one uv workspace and one environment at `98_tools/`. Import rules are tested: apps build on libraries only, never on each other; the command line no longer needs the viewer's code.
- Release building (`package`, `leakscan`, fixtures) moved to the developer's `90_devkit/`, which never ships (the build refuses any `90_`–`95_` folder). Export and release builds share one leak-scanner implementation.
- `init` also copies the tools, launchers and hooks it came with, and writes the kernel version into `aicowork.yaml`.
- One download for new users: `aicowork-<version>.zip` holds the kernel and the tools (the separate kernel and tools zips remain, for the specification alone and for upgrades). The launchers run on plain Python 3.9+ when `uv` is not installed (everything but the viewer).
- Versions may carry a pre-release suffix (`0.0.1-rc.1`); `upgrade` orders them correctly (rc.1 < rc.2 < 0.0.1).

### Known limits

See `SECURITY.md` "What we do NOT claim". In short: the assistant's provider sees what the assistant reads; there is no protection against an owner who sets out to leak their own data; no external security review yet.
