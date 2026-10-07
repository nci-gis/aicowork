# Host page — Claude Cowork

_Ring: host adapter (not kernel). How Claude Cowork meets `99_system/host-contract.md`. Every fact carries its evidence and date; re-verify at each release._
_Tags: **V** = verified in a session on this instance · **D** = Anthropic documentation (date read) · **S** = secondary source or bug report · **?** = not yet verified._

Last full verification: **not yet run** — the host spike (below) is pending. Facts marked V come from earlier sessions recorded in this repo.

## How Claude Cowork meets the contract

| #   | Contract item    | Status | Notes                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --- | ---------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | instruction file | S · ?  | Root `CLAUDE.md` appears to be loaded (from the second message, as a system reminder); `@imports`, nested and `CLAUDE.local.md` are not followed (community report, 2026). `AGENTS.md` only "in a folder with no CLAUDE.md" (changelog 2026-09-21, may apply to the Code tab only). **Use:** root `CLAUDE.md` = the text of `99_system/instruction-file.md`, self-contained.                                              |
| H2  | skills           | D · ?  | Cowork loads skills enabled on the claude.ai account (Customize > Skills), synced at session start; it does not read `~/.claude`. Folder `.claude/skills/` discovery is **unproven**. **Use:** keep `.claude/skills/<name>/SKILL.md` thin pointers (harmless); and install account-level stubs built by `aicowork skills pack`, each saying "read and follow `99_system/skills/<name>/SKILL.md` in the connected folder". |
| H3  | files            | V      | Folder mounted in a Linux VM at `$HOME/mnt/<folder-name>` (also seen: `/sessions/<name>/mnt/<dir>/`); agent works through its shell tool (`device_bash`) and file tools. **Deletion is blocked or needs approval** — never-delete makes this moot. Git on the mount cannot remove its own lock/tmp files (see Quirks).                                                                                                    |
| H4  | scheduled prompt | V · D  | Cloud-run tasks cannot see a local folder; device-bound tasks are suspended when the PC is absent (`device_absent`) and were observed not to resume (2026-09, two of three tasks). **Use:** one-line prompts pointing at `99_system/tasks/*.md`; expect to restart a suspended task by hand.                                                                                                                              |

## Tools inside the host

- **V (2026-10-01, app 2.16120.0):** the VM has `python3` 3.10.12, `git` 2.34.1 and `uv` 0.12.13; `uv` could not fetch a newer Python (download from GitHub fails TLS: `UnknownIssuer`). The stdlib-only commands ran with that Python then: `AICOWORK_BASE="$PWD" PYTHONPATH=98_tools/apps/aicowork/src python3 -m aicowork conform --level 2` and `doctor`. _(Supersedes the 2026-08 note "the VM cannot run uv".)_
- **V (2026-10-03):** the TLS failure is the network's inspecting proxy, whose certificate is in the VM's system store but not in `uv`'s own. Fix, once per VM home: `mkdir -p ~/.config/uv && printf 'system-certs = true\n' > ~/.config/uv/uv.toml`, then `uv python install <version> --default` with the version `98_tools/pyproject.toml` asks for. `uv` then fetched that Python and installed packages from PyPI. Two limits: the shims land in `~/.local/bin`, which a fresh shell does not put on `PATH` (the git hooks also ask `uv python find`, so they find it anyway); and the VM home is per session (`/sessions/<id>`), so a new session or a scheduled task may need the fix again — **?** re-verify in a fresh session.
- **V (2026-10-01):** the VM sets `SANDBOX_RUNTIME` and the folder is a `fuse` mount; `aicowork anchor` therefore refuses here and `doctor` reports the anchor as "not checkable from here". The trust anchor is created and checked **host-side** (Windows: `aicowork.bat anchor`, `aicowork.bat doctor`), never from a session.
- The full tool set (viewer, tests) runs host-side on Windows (`aicowork.bat`, Python 3.11.9 venv).

## Quirks (learned the hard way)

- **Scheduled tasks: "succeeded" is not evidence (V 2026-10-03).** Three tasks pointing at this folder had no folder bound (`folders: []`); a run reported "succeeded" while the file it should have written (the day's log) did not exist. A cloud run that cannot reach the folder ends quietly. **Use:** bind each task to the computer and the folder ("Require this computer" in the desktop app), and judge a task by the file it writes, never by its run status. One run also stayed open for five days, waiting for an answer: a task that asks the owner something should say so and stop.

- Git on the mount cannot delete its own `.lock` / `tmp_obj_*` files ("Operation not permitted") until the owner grants delete permission for the folder (V 2026-10-01: granted on request, `rm .git/*.lock` then worked for the rest of the session). Without a grant, workaround after a commit: move `.git/*.lock` and `.git/objects/*/tmp_obj_*` into `_to_delete/git-stale-<date>/` (gitignored); the owner empties it by hand. A stale `index.lock` blocks the next commit from any host until moved.
- **V (2026-10-02):** a file the session sends to the chat while a folder is connected is also saved by the desktop app into `<folder>/Claude outputs/`. Those are copies (bundles, drafts), not content: keep the folder out of git with `.git/info/exclude` (instance-local) and empty it once the copy has been applied.
- Windows host: keep the folder on a plain local NTFS path, **not OneDrive** or a cloud placeholder folder (S: truncation and stale-snapshot bugs, 2026).
- Windows update KB5124008 (2026-09-08) cut Cowork off from files; fixed by KB5129195 (2026-09-14) (D, changelog).

## Data handling (read before connecting work data)

- **D (architecture overview, read 2026-10-01):** files the agent opens are processed on Anthropic's servers; cloud sessions become the default on 2026-10-06 for Pro/Max. Treat the connected folder as _sent to the model_ (CONVENTIONS "Reach").
- Compliance API / OpenTelemetry exist for Team/Enterprise and are IT-owned; Anthropic's pages disagree on whether content is captured by default — ask IT to set it explicitly.

## Security posture on this host

- Folder-level `.claude/settings.json` permissions and hooks are **not** a dependable control in Cowork (S: open bugs 2026-03). Real controls are admin/MDM settings — see `claude-cowork-hardening.md`.
- Known attack pattern (S, Jan 2026): an injected instruction in a file makes the agent upload a file with an attacker's API key via `curl`. Mitigation in the kernel: untrusted markers, plan-then-apply for risky moves, post-session `aicowork audit`; on the host: manual-approval mode for triage and a `curl` ask rule (IT).

## Operating modes

- **Inbox triage and anything touching untrusted content:** manual-approval mode; no web browsing in the same session; only the connectors you need.
- **Routine logging (morning brief, weekly review):** automatic approval is acceptable; the task specs touch only `06_logs/` and `INDEX.md`.
- **Degraded mode** (shell/mount down): file tools still work; every skill has a files-only path; run `aicowork audit` host-side afterwards.

## Host spike — to run

Follow `99_system/host-contract.md` "Verifying a host", on a copy of this instance, and fill this table. Status: **partial** — items 3 and 5 observed 2026-10-01 in a session where the folder was connected _mid-session_, which makes items 1 and 2 inconclusive; a fresh session with the folder connected from the start is still needed (owner).

| Item                                                       | Result                                                                                                                              | Date / app version     |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1 instruction file read? when? imports?                    | inconclusive: folder connected mid-session; root `CLAUDE.md` was not delivered to the agent afterwards                              | 2026-10-01 / 2.16120.0 |
| 2 `.claude/skills/` discovered? path-based skill loads?    | inconclusive (same reason): folder skills did not appear in the skill list after connecting                                         | 2026-10-01 / 2.16120.0 |
| 3 list/read/create/move/rename/delete/commit/write `.git`? | list/read/create/`git mv`/commit: yes. Delete (incl. `.git/*.lock`): only after an owner delete grant for the folder                | 2026-10-01 / 2.16120.0 |
| 4 scheduled prompt sees folder? sleep behaviour?           | not proven: three tasks with no folder bound (`folders: []`) reported "succeeded" while no file appeared (see H4, scheduled tasks)  | 2026-10-03             |
| 5 `python3 --version`, `git --version`, network from VM?   | `python3` 3.10.12, `git` 2.34.1, `uv` 0.12.13; GitHub download fails TLS (`UnknownIssuer`); `SANDBOX_RUNTIME` set; folder on `fuse` | 2026-10-01 / 2.16120.0 |
| 5b `uv` behind the proxy                                   | works with `system-certs = true` in `~/.config/uv/uv.toml`; the setting lives in the per-session home                               | 2026-10-03             |
| 6 folder `settings.json` deny rule honoured?               |                                                                                                                                     |                        |
