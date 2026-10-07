# Publishing a release (owner runbook)

The tools build and check; **a person ships.** Nothing here is automatic past step 2.

Two folders are involved and they never mix:

- **the development repository** (this one): kernel, host pages, tools, documents, tests. It holds no owner data, and every commit and push is leak-scanned.
- **the owner's private instance**: notes, personas, projects, and `03_personas/me.md` with the names that must never appear in anything shared. It is never published (`distribution: private`).

The leak gate needs those names, so the development repository is told where the instance is, once, locally (never committed):

```
git config aicowork.denyFrom <path to the private instance>
git config core.hooksPath .githooks
```

0. **Set the version** in one commit: `99_system/VERSION` (`0.0.1-rc.3`), the `version` of every `98_tools/**/pyproject.toml` (`0.0.1rc3`), then `uv lock` in `98_tools/` and `devkit fixtures` (the example instance follows VERSION); the CHANGELOG heading gets the version and date. `package` refuses when any of these disagree.
1. **Build** on a committed, manifest-clean tree: `devkit package` (or `devkit package --deny-from <instance>`; `PYTHONPATH=90_devkit/src python -m devkit …`). It refuses without a deny-list, with drift, or with uncommitted changes. Three zips are built — `aicowork-<v>.zip` (everything; what a new user downloads), `aicowork-kernel-<v>.zip` (the specification alone, no code) and `aicowork-tools-<v>.zip` — and each goes through the leak gate; a failed one is moved to `_scratch/release/refused/`. A `REVIEW-<version>-<date>.md` is written beside the artifacts: hashes, file counts, diff against the last recorded release, and _names the gate does not know_ (tags on the instance's personas and projects). Move real names among them into `check_tokens` in the instance's `me.md` and build again. Clean builds are logged in `.agents/releases/releases.jsonl`.
2. **Read** the review file and `CHANGELOG.md`. Record the decision (version, commit, hashes, what you checked) in your instance's `09_decisions/`.
3. **Tag**: `git tag -s v<version> <commit>`, signed with your own key.
4. **Publish**: a release candidate (`-rc.N`) goes only to testers you choose, by a private channel. A final version: push this repository and the tag, create the release, attach the zips and their `.sha256` files.
5. **Consumers** apply it with `aicowork upgrade aicowork-kernel-<v>.zip --expect-sha256 <published>`, read the printed instance actions (`UPGRADING.md`), then `--apply`. A new user unzips `aicowork-<v>.zip` and runs `aicowork init <folder>` from it instead.

What goes out in the zips: the kernel (`99_system/`), host adapters (`hosts/`), the tools (`98_tools/`, launchers, hooks), release documents. Never in the zips: `.agents/`, git history, anything from an instance.
