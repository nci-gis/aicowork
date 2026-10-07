# Host page — Claude Code

_Ring: host adapter (not kernel). How Claude Code (CLI / IDE extension / desktop Code tab) meets `99_system/host-contract.md`. Every fact carries its evidence and date; re-verify at each release._
_Tags: **V** = verified in a session on this instance · **D** = vendor documentation (date read) · **?** = not yet verified._

Last full verification: **not yet run** — facts below are from the documentation (read 2026-10-02); the spike at the end is pending (owner).

## How Claude Code meets the contract

| #   | Contract item    | Status | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ---------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H1  | instruction file | D      | Reads `./CLAUDE.md` or `./.claude/CLAUDE.md` (and every `CLAUDE.md` above the working directory) at launch; `CLAUDE.local.md` beside it for personal notes. `@path` imports work (up to four hops). `AGENTS.md` is read **only when no `CLAUDE.md` exists** (v2.1.277+). **Use:** root `CLAUDE.md` = the text of `99_system/instruction-file.md`, self-contained (imports would also work here, but the same file serves hosts that don't follow them). |
| H2  | skills           | D      | Project skills are discovered at `.claude/skills/<name>/SKILL.md`. **Use:** the thin pointers already in `.claude/skills/` ("read and follow `99_system/skills/<name>/SKILL.md`") are enough — no account-level stubs needed.                                                                                                                                                                                                                           |
| H3  | files            | D · ?  | Runs on the host with the owner's file system and shell; the working directory is the folder. Deletion and `git` work as for any local process (no VM, no lock-file quirk expected — **?**).                                                                                                                                                                                                                                                            |
| H4  | scheduled prompt | ?      | No scheduler is documented for the CLI itself. **Use:** an OS scheduler (Windows Task Scheduler / cron) that starts a session with the one-line prompt from `99_system/tasks/<name>.md`, or run rituals by hand. Not verified.                                                                                                                                                                                                                          |

## Tools inside the host

The reference tools run natively (`uv` on the host, which provides the Python they need): `doctor --quick` at cold start, `audit` after a session, `verify` before a commit — the full set, not the stdlib subset a VM gets.

## Controls this host can enforce (unlike Claude Cowork)

Claude Code honours settings files, so here the kernel's rules can be **prevented**, not only detected. Precedence (D): managed settings (IT) > command line > `.claude/settings.local.json` > `.claude/settings.json` > `~/.claude/settings.json`. Instructions in `CLAUDE.md` are context, not enforcement; to block an action regardless of what the model decides, use permission `deny` rules or a `PreToolUse` hook (D).

Suggested `.claude/settings.json` for an instance — **not yet tested on this instance (?)**; rule syntax per the settings documentation:

```json
{
  "permissions": {
    "deny": [
      "Edit(./99_system/**)",
      "Edit(./hosts/**)",
      "Edit(./policy.yaml)",
      "Edit(./aicowork.yaml)",
      "Edit(./03_personas/me.md)",
      "Edit(./CLAUDE.md)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(git push *)",
      "Bash(git remote add *)",
      "WebFetch"
    ],
    "ask": ["Bash(git *)", "Bash(rm *)", "Bash(mv *)"]
  }
}
```

Notes: `permissions.defaultMode` values that skip approvals cannot be set from project settings (D); `allow` rules and `additionalDirectories` apply only after the user trusts the folder (D). The owner edits `99_system/` deliberately by removing the deny rule for that session — never the agent.

## The trust anchor on this host (ceiling)

Claude Code runs on the owner's own machine with the owner's profile. That is where the trust anchor lives (`~/.local/state/aicowork/anchors`, `%LOCALAPPDATA%\aicowork\anchors`), so an agent session here can read it — and, with the host's shell, rewrite it. On this host the anchor is **tamper-evident, not tamper-proof** (SECURITY, threat 10): `doctor` and the viewer show drift, `export` and `backup` refuse on it, but an agent that is allowed to run shell commands could re-anchor after changing the policy. What keeps it honest here is the host's permission boundary (ask on shell commands; the hardening page) and the post-session `audit`. An anchor outside the machine is not built (SECURITY "not claimed").

## Data handling

Files Claude Code reads are sent to the model provider under the account's terms (same as every hosted model). Treat the folder as _sent to the model_ (CONVENTIONS "Reach"). Approved for this instance's owner: see `policy.yaml` → `ai_surfaces` (`claude-code`).

## Host spike — to run (owner)

| Item                                                                           | Result | Date / version |
| ------------------------------------------------------------------------------ | ------ | -------------- |
| 1 `CLAUDE.md` read at launch? does the agent follow step 3 (`doctor --quick`)? |        |                |
| 2 `.claude/skills/` pointers listed and followed?                              |        |                |
| 3 delete / move / commit / `.git` writes behave like a normal process?         |        |                |
| 4 the suggested deny rules block an edit to `99_system/` and a `curl`?         |        |                |
| 5 L3-REDTEAM with the settings above: audit clean?                             |        |                |
