# Host page — GitHub Copilot (VS Code agent mode, Copilot CLI)

_Ring: host adapter (not kernel). How GitHub Copilot meets `99_system/host-contract.md`. Every fact carries its evidence and date; re-verify at each release._
_Tags: **V** = verified in a session on this instance · **D** = vendor documentation (date read) · **?** = not yet verified._

Last full verification: **not yet run** — facts below are from GitHub's documentation (read 2026-10-02); the spike at the end is pending (owner).

## How Copilot meets the contract

| #   | Contract item    | Status | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --- | ---------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | instruction file | D · ?  | Repository instructions: `.github/copilot-instructions.md`; path-specific `.github/instructions/*.instructions.md`; agent instructions from `AGENTS.md` files (anywhere in the repo) or a single root `CLAUDE.md` / `GEMINI.md` (D). Which of these VS Code agent mode reads at session start is **?**. **Use:** keep the root `CLAUDE.md` (already the instruction file); if the spike shows VS Code does not read it, add `.github/copilot-instructions.md` with the same text. |
| H2  | skills           | D      | Agent skills are read from `.github/skills`, `.claude/skills` or `.agents/skills` in the repository, and work in agent mode in VS Code, the Copilot CLI, the cloud agent and code review (D). **Use:** the existing `.claude/skills/` pointers serve Copilot too. **Never** put a `skills/` folder under this repo's `.agents/` (the dev workspace) — Copilot would load it.                                                                                                      |
| H3  | files            | ?      | VS Code agent mode works on the open workspace with the editor's file tools and terminal on the host. Not verified here.                                                                                                                                                                                                                                                                                                                                                          |
| H4  | scheduled prompt | —      | No scheduler. Rituals (morning brief, weekly review) run by hand: say the task's one-line prompt.                                                                                                                                                                                                                                                                                                                                                                                 |

## The limit that matters most

**Content exclusion does not apply to agent mode or the Copilot CLI** (D: "GitHub Copilot CLI and Agent mode in Copilot Chat in IDEs do not support content exclusion"), and content exclusion itself needs Copilot Business or Enterprise, set by repository/organisation admins (D). So for an AI-Cowork folder opened in agent mode, **everything in the folder reaches the model** — exactly the kernel's reach rule. Nothing must be in the folder that may not reach Copilot's provider; `policy.yaml` → `ai_surfaces` records `github-copilot` with `max_visibility: private` for this instance (MIS-approved 2026-10-01).

## Controls

Copilot does not read the kernel's rules as enforceable settings; treat every rule as **detect and prove**: run `aicowork audit --since <commit>` after an agent-mode session that touched the inbox, and keep the pre-commit / pre-push hooks on. VS Code's own approval prompts for terminal commands are the host's control (?).

## Host spike — to run (owner)

| Item                                                                                                                          | Result | Date / version |
| ----------------------------------------------------------------------------------------------------------------------------- | ------ | -------------- |
| 1 which instruction file does VS Code agent mode read at start (`CLAUDE.md`? `.github/copilot-instructions.md`? `AGENTS.md`)? |        |                |
| 2 are `.claude/skills/` pointers listed and followed?                                                                         |        |                |
| 3 list/read/create/move/commit in the folder? terminal commands ask first?                                                    |        |                |
| 4 L3-REDTEAM in agent mode: audit clean?                                                                                      |        |                |
