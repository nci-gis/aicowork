# AI-Cowork

_You do not need to know anything about AI to read this page. If you only read one page, read this one._

## What this is

A way to keep your notes, plans, people and projects in **ordinary text files in one folder**, and to let an AI assistant work in that folder with you — sorting what you drop in, preparing your day, drafting a reply — **under rules written down in advance**.

The rules are the heart of it. They are a few pages of plain text (the folder `99_system/`, called the _kernel_). They say how the folder is laid out, what the assistant may do, what it must never do, and how anyone can check afterwards that it behaved. No program is needed for the rules to hold: an assistant that reads them follows them. The small programs that come with this (the folder `98_tools/`) only make checking faster. You can ignore them.

## What it does for you

- Your files stay **yours and readable**: open them with any text editor, today or in ten years, with or without the assistant.
- **Nothing is deleted.** Old things are moved to an archive folder. If something goes wrong, the history is still there.
- **The assistant makes no copies of your files elsewhere, except one: the AI service itself reads what the assistant opens** (see the first point under "What it does not promise"). Where other copies may go — a backup disk, a shared folder — is written in one file (`policy.yaml`) that only you edit. Until you have written your decision there, no such copy is made at all.
- Everything you keep is **private unless you, personally, mark it otherwise.** The assistant may never raise that mark.
- Text that arrives from outside — an e-mail, a web page, a file someone sent — is treated as **information, never as instructions**, even when it is written to look like instructions to the assistant.
- After the assistant has worked, you can **see exactly what changed**, file by file.

## What it does not promise

Please read this part as carefully as the one above.

- **The assistant's provider sees what the assistant reads.** When you connect this folder to an AI service, the files the assistant opens are sent to that service under _its_ terms. These rules cannot see or stop that. Only put in the folder what you would show that service, and ask your employer which services are allowed if the folder holds work.
- It is not a promise of secrecy against someone who sets out to break it — including yourself. It is a set of rules that are checked, with a record of what happened.
- It has not been reviewed by a security firm, and it is not a certified product. What has been tested, and how, is listed in `SECURITY.md` and `docs/controls.md`, with the words "not claimed" where something was not.
- It is the first version, 0.0.1 (a copy marked `-rc` is a release candidate, for testing). It is small on purpose. It will be improved; the rules above are the part that will not be loosened.

## The safest first step

1. Make an **empty folder** on your own computer — not inside a cloud-synced folder.
2. Put the rules into it, one of two ways:
   - **With the small programs**: unzip `aicowork-<version>.zip` anywhere, open a terminal in that folder and run `./aicowork.sh init <your-folder>` (on Windows: `aicowork.bat init <your-folder>`). It ends by printing what to do next. It creates the folders and the files the rules need (`INDEX.md`, `aicowork.yaml`, `policy.yaml`, `modules.lock`, `03_personas/me.md`, the instruction file `INSTRUCTIONS.md`) and copies the programs too. They need Python, nothing else — the launcher tells you if yours is too old; with [uv](https://docs.astral.sh/uv/) installed, it fetches the right one for you.
   - **With files only**: copy the folder `99_system/` from this release into it. The assistant creates the other files in step 3.
3. Connect the folder to an AI assistant that **you or your employer have approved**, and point it at the instruction file: `INSTRUCTIONS.md` at the top of the folder, or, with files only, `99_system/instruction-file.md`. With files only, your first request is: _"rebuild AI-Cowork following 99_system/REBUILD.md"_, followed in the same message by the answers its table "Inputs from the owner" asks for (your name and organisation, your roles, and whether this computer is your own or your employer's).
4. Open `03_personas/me.md` and check it: your name, and in `check_tokens` the names of your organisation and of the people that must never appear in anything you share, on one line, like `check_tokens: [Example Co, Minh Tran]`. Fill the empty `Name:` and `Org:` fields and replace every `<…>` placeholder left in it (with files only, any `{{…}}` too). Until this file reads cleanly, every export refuses.
5. Drop one harmless note into `00_inbox/` and say: _"triage my inbox."_ Look at what it did. That is the whole loop.

Steps 1–2 send nothing anywhere. From step 3 on, one thing leaves your computer: **the files the assistant opens go to the AI service you connected**, under its terms (see "What it does not promise"). Nothing else is copied anywhere until you decide it in `policy.yaml`.

## Where the details are

| You want to…                                     | Read                                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| understand the rules themselves — why, what, how | `99_system/README.md`, then `PHILOSOPHY.md`, `CONVENTIONS.md`, `REBUILD.md` in that folder |
| know what "working correctly" means and check it | `99_system/conformance/SUITE.md`                                                           |
| use the small programs (checks, a local viewer)  | `98_tools/README.md`                                                                       |
| connect a particular AI assistant                | `hosts/README.md`                                                                          |
| know the risks and what is not claimed           | `SECURITY.md`, `PRIVACY.md`, `docs/controls.md`                                            |
| compare with other tools, honestly               | `docs/COMPARISON.md`                                                                       |
| publish a release, or install a newer one        | `docs/publishing.md`, `UPGRADING.md`                                                       |
| know what changed                                | `CHANGELOG.md`                                                                             |

The kernel (`99_system/`), the host adapters (`hosts/`) and the small programs (`98_tools/`) are released under the MIT licence (`LICENSE` in each folder).
