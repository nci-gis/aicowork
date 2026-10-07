# AGENTS.md — Agent Knowledge Base

> The heart. Every harness stub points here, so this file is loaded into every
> session and competes with the task for context. **Keep it under 100 lines.**
> Detail belongs behind a trigger, not here.

---

## Load first

1. **[FIXED-POINT.md](FIXED-POINT.md)** — the main philosophy of this repository. Every change is judged against it.
2. **This file.**
3. **`context/project.md`** — what this repository is and its rules (every session).
4. The other files in `context/` that your task touches. Read a `context/` file when
   the work is in its subject, not because it exists.
5. Files in `reference/` when their stated trigger fires — each one
   opens with a **Read this when** line.

Everything else is **on demand**, including `prompts/`, which are invoked
deliberately rather than loaded at startup.

Context spent here is context taken from the task, so load by relevance, not
by habit. Loading everything is a cost, not thoroughness.

**Conflict resolution**: `context/` is authoritative over everything else.

---

## Directory map

```text
.agents/
  FIXED-POINT.md # The main philosophy — read first, owner-only
  AGENTS.md      # This file — loaded every session
  reference/     # Topic docs, each with its own trigger
  context/       # Canonical knowledge (human-curated, authoritative)
    project.md            # What this repository is, its rules — read every session
    philosophy.md         # How we develop: the principles that decide close calls
    harness-behaviour.md  # How the harnesses load and enforce (dated)
    memory-placement.md   # Which memory system a finding belongs in
  memory/        # Agent-generated learnings (drafts) — see _TEMPLATE.md
  prompts/       # Scanning & generation prompts — invoked, not auto-loaded
  skills/        # Reusable procedures (Agent Skills spec)
  plan/          # PDCA.md, promotions.md, cycles/, v0.0.1-plan.md (release track), backlog.md (triggers)
  decisions/     # Design decisions (dated records, why + when to revisit)
  releases/      # Release log written by `devkit package` (do not edit)
```

---

## Authority

| Path                                                                                                                   | Agents may                                                         |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `FIXED-POINT.md` (owner only), `AGENTS.md`, `reference/`, `context/`, `prompts/`, `skills/`, `decisions/`, `releases/` | ❌ READ ONLY                                                       |
| `memory/`                                                                                                              | ✅ READ + WRITE                                                    |
| `plan/`                                                                                                                | ⚠️ APPEND to `promotions.md`; edit `Do`/`Check` of an active round |

Closing a round, editing a closed one and compacting `cycles/` are human calls — see [plan/PDCA.md](plan/PDCA.md).

Enforcement is per harness; today only Claude Code has any: `.claude/settings.json`
makes it **ask** before an `Edit` under `.agents/` (except `memory/`), `99_system/`, `hosts/` and `.githooks/`. A speed bump, not a wall — one
tool, interactive only, shell writes bypass it. Codex, Gemini and Copilot read this
table as text; nothing backs it yet — see [context/harness-behaviour.md](context/harness-behaviour.md).

**A human may still authorise a change** — warn first, wait for confirmation,
log it in `plan/promotions.md`. Procedure:
[reference/memory-and-promotion.md](reference/memory-and-promotion.md).

**If a discovery contradicts `context/`**: do not edit it. Write the finding to
`memory/` and flag it for human review.

**If `memory/` looks outdated**: do not delete it. Add
`**Status**: Needs Review` to its header.

---

## Write policy

Agents MAY:

- ✅ Capture reusable insights in `memory/`
- ✅ Suggest promotions to `context/` or `skills/`, inside a memory file

Agents MUST NOT:

- ❌ Store secrets, credentials, or personal data — here that includes any real name, organisation, path or e-mail: this repository will be public and `devkit leakscan` refuses the commit
- ❌ Write to any read-only path above without explicit human instruction
- ❌ Generate speculative rules without concrete evidence

---

## Where to look for more

| Read this                                                              | When                                                 |
| ---------------------------------------------------------------------- | ---------------------------------------------------- |
| [reference/memory-and-promotion.md](reference/memory-and-promotion.md) | Writing a memory file, or proposing a promotion      |
| [reference/root-files.md](reference/root-files.md)                     | Editing `CLAUDE.md`, `AGENTS.md` or any harness stub |
| [reference/mechanisms.md](reference/mechanisms.md)                     | Choosing between a rule, skill, hook or sub-agent    |
| [reference/skills.md](reference/skills.md)                             | Authoring or fixing a `SKILL.md`                     |
| [context/harness-behaviour.md](context/harness-behaviour.md)           | Relying on how a harness loads, enforces or budgets  |
| [context/memory-placement.md](context/memory-placement.md)             | Saving a memory, and unsure which system it goes in  |
| [context/philosophy.md](context/philosophy.md)                         | A judgement call the rules above do not cover        |
| [plan/PDCA.md](plan/PDCA.md)                                           | Opening or closing a round                           |
