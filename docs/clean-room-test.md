# Clean-room test — for the person who tries this first

_You are the test. You do not need to know anything about AI or programming. If a step does not work as written, that is a finding about the text, not about you — write it down and stop; do not look for a workaround._

## What you need

- A computer of your own (not shared), with about an hour.
- The file `aicowork-<version>.zip` and its `.sha256` file, from the person who asked you to test. Nothing is downloaded from anywhere else, except by the small program in step 2 if you let it (see there).
- One AI assistant you are allowed to use — the person who asked you says which. If you have none, you can still do steps 1, 2 and 4.

## The five steps

They are the same five as in `README.md`, "The safest first step". Do them from that page, not from memory. Below is only what to write down at each.

| Step | Do                                                                                        | Write down                                                                                                                                                                         |
| ---- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Make an empty folder.                                                                     | Where you made it. Whether you wondered what "cloud-synced" means.                                                                                                                 |
| 2    | Unzip the file, open a terminal in the unzipped folder, run the command the README gives. | The exact command you typed and the last 5 lines it printed. Whether it asked you to install Python or `uv`, and what you did. Whether the "next, in that folder" list made sense. |
| 3    | Connect the folder to the assistant, as `hosts/README.md` says for yours.                 | Which page you read, which file you pointed the assistant at, and the first thing the assistant said. Whether it ran a health check by itself.                                     |
| 4    | Open `03_personas/me.md` and fill it in.                                                  | Every placeholder you were unsure about. Whether "check_tokens" was clear.                                                                                                         |
| 5    | Drop one harmless note into `00_inbox/` and say _"triage my inbox."_                      | What the assistant said it did, and where the note ended up (look in the folders). Whether it asked you to do something, and whether you understood what.                          |

## The question log

Every time you have to stop and think "what does this mean?", add a line. One line per question; the number of lines is the result.

```
| # | Step | What I read | What I understood / did not | What I did next |
|---|------|-------------|-----------------------------|-----------------|
| 1 |      |             |                             |                 |
```

A question you answered yourself still counts. A step you could not finish counts most.

## What to send back

The log above, the lines you wrote down per step, and nothing from the folder itself (its contents are yours). The person who asked you turns each line into a change to the text or a test, and shows you the result.

## Known before you start

Found on 2026-10-09 by a dry run of these steps on Linux, already fixed in the text you hold if your version is newer than 0.0.1-rc.6; if not, you will meet them:

- The command is `./aicowork.sh init <your-folder>` on Linux and macOS, `aicowork.bat init <your-folder>` on Windows — not a bare `aicowork`.
- Your first commit asks "who you are"; the program's "next, in that folder" list tells you the two lines to run.
- `me.md` has `<…>` placeholders and empty `Name:` / `Org:` fields, not `{{…}}`.
- Use your own names in `check_tokens`, not the README's example ones: `Example Co` is the name the rules themselves use for a made-up company, so with it in `check_tokens` the check reports the rules file as a leak.
