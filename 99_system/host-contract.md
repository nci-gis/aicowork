# Host contract

_Kernel. What any host — an agent app, an IDE assistant, a CLI agent — must provide for AI-Cowork to work in it. Four things, nothing more. A host page in `hosts/<host>.md` records how one host meets each item, with the date and host version it was verified on._

| #   | The host must…                                                                                                                    | The kernel relies on it for                     | If the host cannot                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------- |
| H1  | **read an instruction file from the connected folder** at session start (or accept the same text in a project-instructions field) | the cold start: `99_system/instruction-file.md` | paste the instruction-file text into the host's instructions field  |
| H2  | **load skills** — from the folder, or through a stub installed in the host that points into the folder                            | procedures in `99_system/skills/`               | the owner says "read and follow `99_system/skills/<name>/SKILL.md`" |
| H3  | **read and write files in the connected folder** (list, read, create, move; git if available)                                     | everything                                      | not a host for AI-Cowork                                            |
| H4  | **run a scheduled prompt** (optional: the system works without it, rituals then start by hand)                                    | task specs in `99_system/tasks/`                | start rituals by hand ("morning brief")                             |

## What the kernel does NOT assume

- that the host honours permission files, hooks or sandbox settings shipped in the folder;
- that any tool (Python, git, a CLI) runs inside the host — tools accelerate, never gate; every procedure has a files-only path;
- that deletion works (never-delete makes this moot);
- that the host keeps the folder's content on the machine — see CONVENTIONS "Reach".

## Verifying a host (the host spike)

Run in a fresh session on a copy of an instance, record in the host page:

1. H1 — which instruction file is read, and when (first message? later?). Are `@imports` or nested files followed?
2. H2 — are skills inside the folder discovered by the host's own skill mechanism? Does a path-based skill load?
3. H3 — can the agent list, read, create, move, rename, delete, `git commit`, write inside `.git/`? What does a delete prompt look like?
4. H4 — does a scheduled prompt see the local folder? What happens when the machine sleeps or is absent?
5. Tools — which interpreters exist (`python3 --version`, `git --version`)? Is the network reachable from the tool sandbox?
6. Controls — does the host honour folder-level permission/hook files? (Test with one deny rule.)
   A new host is supported when its page exists and the kernel needed **no change** to pass conformance L3 there.
