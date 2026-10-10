# Changelog

## Unreleased — the gates: clean-room findings, the rebuild drill, two leak-gate fixes

Round 001 ran the open gates of 0.0.1: the five README steps from the rc.6 zip, a rebuild from the kernel text alone, the Claude Code host page. What follows is the short form; the full notes with the evidence are in `docs/releases/unreleased.md`.

- **The kernel** (owner): a triage may end with a plan for the owner, and L3-TRIAGE scores it so; the instruction file and the triage skill name the launcher an instance has (`./aicowork.sh`, `aicowork.bat`); REBUILD §0, §1 and §3 made exact where the rebuild drill had to guess; SUITE L1-FRONTMATTER excludes `README.md`; `tags` are lower-case slugs and the link between items (a project's slug is its tag; `related:` the explicit pointer), SUITE checks their shape, and the triage skill gives a filed note the tags it shares with what it relates to. Kernel documents: measured at the version-set commit.
- **Security**: `allow_tokens:` can no longer silence an explicit `check_tokens` entry and is bound to the trust anchor (C35) — run `aicowork anchor` once after upgrading; the leak scans now read the author and committer of every pushed commit, and the identity this clone would sign the next commit with (C36).
- **Finding things** (Round 002): tags are the link between items — a tag shared by two notes links them, a tag is a group, a project's slug is its tag — and `related:` stays the explicit pointer. The viewer lists tags in the sidebar with open counts, filters Browse by tag, and shows on each item what it is linked to (its `related:`, what points at it, open items sharing a tag); `aicowork tags` is the files-only view; a tag that is not a slug gets an L1 warning. The kernel's sentences for it are the owner's (`.agents/memory/2026-10-10-tags-link-decision-draft.md`).
- **Reference tools**: the viewer opens on open items and counts them; `init` ends with commands a new owner can type; `triage --apply` sets the `Last triage:` footer and says how to commit; a plan cannot file a raw item where frontmatter is required; `06_logs/triage/` is part of the skeleton; `sbom --out` creates its folder.
- **Documents**: README steps 2 and 4 as a new owner meets them; `docs/clean-room-test.md` for the tester of gate G5; `docs/dpia-lite.md` is a template; `hosts/claude-code.md` H1, H3 and H4 verified.
- **The repository**: CI on every push and pull request; the CHANGELOG is hand-written and checked; the release log keeps hashes, not file lists.

## 0.0.1-rc.6 — 2026-10-08 (release candidate, not for publication) — the viewer and the apps

Full notes: `docs/releases/0.0.1-rc.6.md`.

- **The kernel**: a triage that would move many items or touch `03_personas/` or `09_decisions/` ends with a plan the owner applies (`06_logs/triage/`); topic watch — a task, a skill, templates, L3-WATCH — files sourced, untrusted results; a `service` app may carry a `command`, started by the owner with `aicowork app <id>`; the weekly review may hint that a recurring lesson is ready to become a practice. Kernel documents: 7,897 of 10,000 words.
- **Reference tools**: plan Review/Apply in the viewer and `aicowork triage --apply` share one rule set; a lesson's `[context]` that names a file is a link; lessons resurface on this day; `aicowork new watch`, `aicowork app`; fix: `reminders --week` without a value.

## 0.0.1-rc.5 — 2026-10-08 (release candidate, not for publication) — reminders complete, honest dry-runs

Full notes: `docs/releases/0.0.1-rc.5.md`.

- **The kernel**: `notice:` on a reminder (days of warning); Keep an eye ordered overdue → due → hot → upcoming, at most five lines; reminders missed this week counted from git, or "not computable"; decision record `kernel-host-viewer-and-apps`. Kernel documents: 7,805 of 10,000 words.
- **Security**: a dry run of `backup` or `export` runs the binding gate like the real run (C34).
- **Reference tools**: `aicowork reminders` with `--week` and `--json`; `recur` knows `notice`.
- **The repository**: public from here on (MIT `LICENSE`); `devkit leakscan` and the hooks run in a contributor's clone with the generic patterns.

## 0.0.1-rc.4 — 2026-10-06 (release candidate, not for publication) — reminders

Full notes: `docs/releases/0.0.1-rc.4.md`.

- **The kernel**: reminders, a tenth content type for dated duties that repeat — one file per duty in `10_reminders/`, nine occurrence rules so every implementation computes the same answer, `last_done` as the only state; out of the circle-balance chart. Kernel documents: 7,356 of 10,000 words.
- **Security** (red-team of 2026-10-06, controls C28–C31): the trust anchor binds every file that steers the agent and egress refuses on drift — owner action `aicowork anchor`; a sender's `visibility: public` is made private on filing; owner names hidden by look-alike characters or encodings are matched after normalisation and hidden characters are reported; symlinks are reported, never followed; INDEX titles are checked.
- **Reference tools**: the occurrence rules once, in `aicowork_core.recur`; conformance, `init`, `doctor` and triage know reminders; the viewer lists them in Keep an eye with a Done button.

## 0.0.1-rc.3 — 2026-10-03 (release candidate, not for publication) — fixes from two reviews of rc.2 and its first real use

Full notes: `docs/releases/0.0.1-rc.3.md`.

- **The kernel**: ambiguity is an error, never a guess — a note that can be read two ways is private and refuses every export (L2-AMBIGUITY, `conformance/ambiguity.json`, a fixture per class); "No export leaves silently"; `decided:` is the owner's alone, never an agent's; REBUILD lists the exact `.gitignore` and `.gitattributes`; the 10,000-word budget counts six documents; module files sort by code point on every OS; retired kernel files are not notes.
- **Reference tools**: one strict frontmatter parser; private blocks found by their grammar; the same bytes and hashes on every OS; `aicowork decide` at the owner's own terminal; `upgrade --apply` records what it wrote and `audit` accepts exactly that; `doctor` names uncommitted paths; upgrade from rc.2 with the rc.3 tools; `init` writes `## Practices`, `modules.lock` and the first commit; the viewer's search bar and dashboard share one centred column.

## 0.0.1-rc.2 — 2026-10-03 (release candidate, not for publication)

Supersedes rc.1 (built the same day, never installed): the first candidate of the first versioned release. Full notes: `docs/releases/0.0.1-rc.2.md`.

- **The kernel**: a specification, not software — a five-point membership test, four rings, English, at most 10,000 words; PHILOSOPHY, CONVENTIONS, REBUILD, the host contract, the instruction file, schemas, policy presets, templates, three skills, scheduled tasks, the `7habits` module, conformance L1–L3 with a fictional example instance.
- **Host adapters**: Claude Cowork verified 2026-10-01, with a hardening guide for IT; Claude Code and GitHub Copilot documented, not verified.
- **Reference tools** (optional): the `aicowork` command (standard library, Python 3.9+) and an offline viewer; nothing leaves the folder except through `backup` and `export` under `policy.yaml`, each with a hash-chained receipt; export is content-checked, `below: encrypt` seals what must not travel in clear; `upgrade` checks the published sha256; no network connections (tested).
- **The repository**: the kernel's own repository, holding no owner data, leak-scanned on every commit and push; `98_tools/` as libraries and apps in one environment; `90_devkit/` builds releases and never ships; one download for new users; pre-release versions ordered.
- **Known limits**: SECURITY "What we do NOT claim".
