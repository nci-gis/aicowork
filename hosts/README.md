# hosts/ — connecting an AI assistant

_Host adapters: not part of the kernel. The kernel says what any assistant host must provide (`99_system/host-contract.md`, four things); each page here says how one particular host meets it, with the date it was last verified._

| Host                                     | Page                | What you need to know first                                                                                                                                                            |
| ---------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Cowork (desktop app)              | `claude-cowork.md`  | the files the assistant opens are sent to the provider; folder-level settings in the app are not a dependable control; a hardening list for your IT is in `claude-cowork-hardening.md` |
| Claude Code (CLI, IDE, Code tab)         | `claude-code.md`    | honours `.claude/settings.json`: the kernel's rules can be enforced with deny rules and hooks, not only detected (documented; not yet verified here)                                   |
| GitHub Copilot (VS Code agent mode, CLI) | `github-copilot.md` | content exclusion does **not** apply to agent mode or the CLI: everything in the folder reaches the model (documented; not yet verified here)                                          |

No page for your host yet? The kernel still works: give the assistant the text of `99_system/instruction-file.md` at the start of every session, and verify the four items of the host contract yourself ("Verifying a host" in `host-contract.md`). A page that has not been verified on a date is not a claim of support.
