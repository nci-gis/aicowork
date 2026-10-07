# AI-Cowork — development repository (instructions for agent sessions)

<!-- a2scaffold:start -->

> Claude Code reads this file, not `AGENTS.md`. It is a stub: the project
> knowledge lives in `.agents/`, imported below.

## Shared knowledge base

`.agents/` holds the directory layout, authority rules, load order, and the
pair-programming workflow. Treat it as part of these instructions.
Agents that expand `@` imports load it inline; others open it directly.

@.agents/AGENTS.md

<!-- a2scaffold:end -->

**Read first: the fixed point** — the main philosophy of this repository; every change is judged against it.

@.agents/FIXED-POINT.md

This repository develops the **AI-Cowork kernel** and its reference tools; it holds **no owner data, ever**. Project rules: `.agents/context/project.md` (loaded through `.agents/AGENTS.md`).
