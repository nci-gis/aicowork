# Upgrading an instance

`aicowork upgrade <release.zip> --expect-sha256 <published sha256>` shows the diff; `--apply` installs it (clean git tree required; a bundle is taken first; removed files go to `07_archive/`; instance files are never touched except `kernel_version` in `aicowork.yaml`). The tools never fetch: you download or clone the release yourself, then point `upgrade` at it. Each section below lists what **you** must change in the instance by hand for that version — `upgrade` prints it and does not do it.

## 0.0.1-rc.6

No action is required. Three things you may want:

1. Restart the viewer once: its cache rebuilds by itself (schema 5 → 6).
2. A project you want watched gets a `watch.md` (`aicowork new watch --slug <project>`): topics, queries, cadence. The `topic-watch` task needs a host with a search tool.
3. A service you start by hand can be registered under `apps:` with `kind: service`, its loopback `target` and a `command` (a list of words); `aicowork app <id>` starts it from your terminal. The example in `99_system/aicowork.example.yaml` shows the shape.

Create `06_logs/triage/` (with a `.gitkeep`): REBUILD §1 lists it, so conformance L1-SKELETON checks it (the first plan would otherwise create it, but the check does not wait for that).

## 0.0.1-rc.5

No action is required. Two things you may want:

1. Add `notice: <days>` to a reminder that deserves a longer (or shorter) warning than the dashboard horizon — a yearly renewal, say `notice: 30`. Leave it empty and nothing changes.
2. The weekly review template now has `Reminders done / overdue / missed`; existing weekly files are not touched. The number needs git history (`aicowork reminders --week` prints it); without git the review says "not computable".

## 0.0.1-rc.4

A new content type, **reminders**: dated duties that repeat (CONVENTIONS "Reminders").

1. Create the folder `10_reminders/` (`aicowork doctor` and conformance L1-SKELETON say so while it is missing).
2. Add a `## Reminders` section to `INDEX.md`, between Practices and Decisions (conformance L1-ROOT checks it). With these two, conformance passes again with zero reminder files.
3. Move recurring duties you filed as practices or as repeated events into reminders: one file per duty in `10_reminders/<slug>.md`, from `99_system/templates/<lang>/reminder.md` (`repeat`, `days`, `date`, optional `until`; leave `last_done` empty), listed under `## Reminders`. Move the originals to `07_archive/` — move, never delete. A practice measured by presence stays a practice.
4. Restart the viewer once: its cache rebuilds by itself (schema 4 → 5).
5. **Run `aicowork anchor` on your own computer** (not from an agent session). The trust anchor now binds every file that steers the agent — `policy.yaml`, the `security` block of `aicowork.yaml`, the instruction file, your `check_tokens`, `modules.lock` — and `export` and `backup` refuse until the policy is anchored, or when it changed since. `aicowork decide` anchors by itself from now on; after you edit one of those files on purpose, run `aicowork anchor` again. `doctor` and the viewer say when one drifted.

## 0.0.1-rc.3

- **From 0.0.1-rc.2, run the upgrade with the new release's tools**, not the instance's own: unzip `aicowork-0.0.1-rc.3.zip` anywhere and, from that folder, run `aicowork upgrade <the zip> --expect-sha256 <published sha256> --base <your instance>` (dry run, then `--apply`). rc.2's `upgrade` loads part of the new code halfway through and stops with an `ImportError`; if that already happened, put the half-applied files aside with `git stash -u` (nothing is deleted; the pre-upgrade bundle in `_scratch/` holds the state before too), then upgrade again as above. From rc.3 on, an instance's own tools upgrade it.
- Retired kernel files belong in `07_archive/kernel-<name>/` (where `upgrade` puts them): they are not notes, so conformance does not judge them and export never takes them. If you archived an old kernel copy elsewhere yourself (its templates hold `{{…}}` placeholders, which conformance L2-AMBIGUITY now refuses), move that folder under `07_archive/kernel-<name>/` — move, never delete.
- Add a `## Practices` section to `INDEX.md`, between Projects and Decisions (REBUILD §1; conformance L1-ROOT checks it). List your `08_practices/` notes there, or leave it empty.
- Run `aicowork modules --lock` once after upgrading. A lock or a ring manifest written on Windows listed files in a different order from one written on Linux, so the same module gave two hashes; every OS now uses one order, and a lock made on Windows changes once. Run `aicowork anchor` on your host afterwards: the trust anchor records the manifests' hashes.
- `03_personas/me.md` must have its frontmatter (`check_tokens:` lives there). A file without one, or a `check_tokens` the strict reader cannot read exactly, now makes every leak gate refuse instead of scanning for nothing; `aicowork doctor` names the line.
- Copy the new text of `99_system/instruction-file.md` into your instruction file (`INSTRUCTIONS.md`, or the file your host reads — see `hosts/<host>.md`): it now says that an agent never writes `decided:` in `policy.yaml`. To decide a policy, add the line yourself, or run `aicowork decide` in your own terminal.
- `.gitattributes`: add `*.cmd text eol=crlf`, `*.pptx binary` and `*.bundle binary` if they are missing (REBUILD §1 lists the whole file). `.gitignore`: `98_tools/data/` is now `98_tools/apps/viewer/data/`.
- Python: the tools ask for the version in `98_tools/pyproject.toml`. With `uv` nothing changes for you; without it, an older Python now gets a one-line message instead of an error deep in the code.

## 0.0.1-rc.2

_(Supersedes 0.0.1-rc.1, which was never installed anywhere. Upgrading from an instance made before 0.0.1: read every point.)_

- `98_tools/` has a new layout: `libs/core/` (the shared library), `apps/aicowork/` (the command line), `apps/viewer/`, and one environment for all of them (`98_tools/pyproject.toml`, `98_tools/uv.lock`, `98_tools/.venv`). `upgrade` installs it and moves the old `98_tools/src/`, `98_tools/tests/` and per-tool lock files to `07_archive/`. Old `.venv/`, `data/` and `__pycache__/` folders under `98_tools/` are caches: delete them by hand; `uv` rebuilds `98_tools/.venv`.
- If your host's instruction file runs the tools without installs, change `98_tools/src` to `98_tools/apps/aicowork/src` there (the library beside it is found automatically).
- Release building moved out of the tools (`aicowork package`, `aicowork leakscan` are gone from instances); it is the kernel developer's devkit, which never ships.
- `kernel_version` in `aicowork.yaml` may carry a pre-release suffix (`0.0.1-rc.2`); `upgrade` writes it for you.
- Add a `README.md` to each content folder: `aicowork init` does it for new instances; for an existing one, run `python -c "from aicowork.instance import ops; print(ops.write_folder_readmes('.'))"` with `98_tools/apps/aicowork/src` on `PYTHONPATH` (never overwrites).
- Templates now ship in English only. An instance with `language.modules.templates: vi` falls back to English templates; set it to `en` (note bodies keep their language).
- `below: encrypt` now works for export destinations (it was refused before); it needs the full tools install (`cryptography`).
- `policy.yaml` gains `distribution: private | controlled`. **Missing = private**, which forbids git remotes and export destinations. An instance that exports or pushes must add `distribution: controlled` deliberately (PHILOSOPHY #11), or drop those entries.
- `policy.yaml` gains optional `compliance.prohibited_markers` (exact strings that must never be inside the folder). Add your employer's classification stamps if any.
- Presets now ship **undecided**: a fresh `policy.yaml` has no `decided:` line until you add it. Existing instances keep theirs.
- Host adapters moved from `99_system/hosts/` to top-level `hosts/`; `upgrade` moves them (the old copies go to `07_archive/`).
- `frameworks/7habits/roles.md` is gone; roles live in `03_personas/me.md`. Scheduled prompts point at `99_system/tasks/<name>.md`.
