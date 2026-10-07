# Design Philosophy — AI-Cowork

_Why the system is shaped this way. Changes rarely. When a trade-off is unclear, this file decides._

## The goal

> **Govern yourself by a written culture and an AI that asks the right question. Then let it spread to the team — by pull, never by push.**

Set 2026-09-11. One ambition at two scales: the metacognition of a person, the culture of a team (Giản Tư Trung: governance by culture; Covey: private victory before public victory; this repo: instance before kernel). The principles below serve this goal — a principle that stops serving it gets rewritten, not obeyed. Culture is measured by what survives without its founder: instances alive after 30 days unprompted, kernel PRs not by the owner, people who edit PHILOSOPHY.md rather than only use it. The moment the kernel is imposed on someone, it stops being culture and becomes policy.

## The kernel

_Added 2026-10-01 (v0.0.1); signed off by the owner 2026-10-01._

**The kernel is a specification, not software.** It is the smallest set of written things such that any competent agent, on any host, with any model, given the kernel and an empty folder, rebuilds a working AI-Cowork without asking the owner. Two people with the same kernel get instances that differ in content but are interoperable in shape. Anyone may write their own tools; an instance that passes the kernel's **conformance suite** (`99_system/conformance/`) _is_ a proper AI-Cowork — whoever built it, with whatever tools.

**Membership test** — a thing belongs to the kernel only if all five hold:

1. **Host-independent** — names no host, IDE, model or provider.
2. **Notepad-readable** — prose, Markdown, YAML or JSON. Understanding it needs no code.
3. **Rebuild-necessary** — remove it and a rebuild fails or diverges. If nothing breaks, it is not kernel.
4. **Owner-independent** — no person, organisation or path.
5. **Testable** — a principle carries a claim label, a contract has a schema, a procedure has an acceptance check.

Everything else sits in one of three outer rings — reference implementation, host adapters, instance (CONVENTIONS "Rings"). Pick carefully: the kernel grows only by a decision entry, and it must stay readable in one sitting.

## The three layers of documentation

| File                   | Answers                                                    | Changes                      |
| ---------------------- | ---------------------------------------------------------- | ---------------------------- |
| `PHILOSOPHY.md` (this) | **Why** — principles that arbitrate trade-offs             | almost never                 |
| `CONVENTIONS.md`       | **What** — the contract: folders, frontmatter, index rules | when content types are added |
| `REBUILD.md`           | **How** — recipe to rebuild from an empty folder           | when tooling changes         |

**Acceptance test**: give the kernel release (these three files say how; the rest of `99_system/` is copied) + an empty folder to a fresh agent session → it rebuilds an equivalent system without asking the owner, and the result passes conformance level 2. Every question the agent has to ask is a defect in the kernel. (Drill: run this quarterly, see REBUILD.md.)

## Principles

1. **Flat files are the source of truth.** Markdown + YAML frontmatter. SQLite (FTS5) is a derived cache — deletable, gitignored, rebuilt from files. Never store state only in the DB.
2. **Git is the audit log.** Nothing is deleted; move to `07_archive/`. Commit prefixes name the event type (the list is in CONVENTIONS, Session rule 7).
3. **Human-first.** Every file must be readable in Notepad. If all tools die, the data still lives. Tools serve files, not the other way around.
4. **One extension point per layer.** Content → add a frontmatter `type` (with its schema). Behaviour → add a module (`module.yaml`, CONVENTIONS "Modules"). Apps → add an entry under `apps:` in the instance's `aicowork.yaml`. Tools → the reference implementation has its own single extension point (a CLI command); other implementations choose theirs.
5. **Capture must be cheap; structure is paid later.** Dropping into `00_inbox/` takes 2 seconds, zero decisions. Triage (by AI) adds structure afterwards. Never force classification at capture time.
6. **Local-first, offline-capable.** No CDN at runtime — tools vendor what they need. The system must work with the network cable pulled. The one egress that cannot be removed is the call to the model; it is named, never hidden (CONVENTIONS "Reach").
7. **The system serves the four circles** — Work · Family · Friend · Health — plus Reflect. A feature that maps to none of them is not built.
8. **Work is measured by output; life is measured by consistency & presence.** Work items may carry status/deadline/KPI. Life items carry cadence and "was I there". Never put KPIs on family.
9. **Small numbers only.** The dashboard shows at most 5 health signals. More metrics = self-deception.
10. **Hub & spokes.** This folder is the cockpit — coverage over depth: triage, rituals, cross-project status, prep, decisions. Deep work (code, review, long writing) happens in each project's own repo with its own session (spoke). The hub holds pointers and deltas, never a project's working files. Boundary is a default, not an electric fence.
11. **Decide when sober.** Every judgment that affects what leaves the machine — the egress policy, a file's `visibility` — is made once, deliberately, in a calm moment, and written down. Execution afterwards is a pure function of those written decisions: no inference at run time, for human or AI alike. The AI may lower or propose; only the human raises. Capture (quick-add, inbox) is the least sober moment in the system, so it carries no such decision at all.
12. **Claims need evidence.** _(Signed off 2026-10-01.)_ Every claim the system makes about itself — in this file, in a release note, in a comparison — carries a label: **Stance** (a chosen value, not testable), **Untested** (falsifiable, not yet tested), **Sourced** (backed by a cited source), **Measured** (backed by a conformance case or a recorded measurement). A claim without evidence is removed, not softened. The kernel detects and proves; it does not pretend to police the host it runs on.

## Claim labels on these principles

Stance: #1, #3, #5, #7, #8, #11, #12 — chosen values. · Untested: #9 ("more metrics = self-deception"), #10 (hub/spoke beats one big repo), and the founding bet below. · Measured by conformance: #1 (cache deletable → L1), #2 (never-delete → L2), #6 (our tools make no network call → tools test), #9 (≤ 5 signals → L2).
**Founding bet (Untested, falsifiable):** a person or team that keeps a human in the loop and writes its culture down learns faster than one that hands the loop to agents. What would falsify it: instances that stop being used within 30 days unprompted.

## Framework Adoption Contract

Any methodology (7 Habits, OKR, GTD, PARA, Ikigai…) is adopted as a **module** (CONVENTIONS "Modules") and gets **at most**:

1. one template folder (the module folder, `99_system/modules/<name>/`)
2. two frontmatter fields
3. one dashboard signal
4. one recurring prompt (daily or weekly)

If it wants more, the framework is hijacking the system — cut it back.

## Not-do list

Multi-user · auth · cloud sync · native mobile app · own notification system · WYSIWYG editor · realtime collaboration. If tempted, re-read principle 3 and 9.
