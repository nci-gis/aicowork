# How AI-Cowork compares — honestly

_Market facts researched 2026-10-01 from vendor pages and security reports (secondary sources marked in the research notes); they change fast — re-check before quoting. Every AI-Cowork cell links to its evidence in `docs/controls.md` (C-numbers) or says "not claimed"._

## Where others are stronger (and we say so)

| Need                                                               | Better choice today                                                    | AI-Cowork                                                                                                                            |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Polished editor, mobile apps, sync                                 | Obsidian, Logseq, Notion, Tana, Capacities                             | not claimed — plain files open in any editor; no mobile, no sync (PHILOSOPHY not-do list)                                            |
| Real-time collaboration                                            | Notion, Microsoft 365                                                  | not claimed — teams join by pull (git), never live co-editing                                                                        |
| Enterprise certifications, tenant DLP, audit logs held by a vendor | Microsoft 365 Copilot + Purview, Notion Enterprise, ChatGPT Enterprise | not claimed — no vendor, no certificate; evidence pack for your own review (`aicowork audit-pack`)                                   |
| Plugin ecosystem                                                   | Obsidian                                                               | not claimed, on purpose — plugins inherit full privileges (Obsidian says it cannot sandbox them); AI-Cowork runs no third-party code |
| Semantic search                                                    | Obsidian plugins, Khoj, Basic Memory                                   | not claimed — full-text only (FTS5)                                                                                                  |

## Where AI-Cowork is built to be stronger

| Property                                                                                    | Typical tools                                               | AI-Cowork                                             | Evidence                              |
| ------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------- |
| The system is a **testable specification** anyone can re-implement                          | the product is the code                                     | kernel = spec; "proper" = passes conformance          | C25, `99_system/conformance/SUITE.md` |
| **Per-file visibility, fail-closed, enforced at egress with receipts**                      | workspace/page permissions, or none                         | `visibility` + `policy.yaml` + hash-chained receipts  | C05–C09                               |
| **Agent sessions audited after the fact, in plain text**                                    | agent actions unlogged, or logged by the vendor             | `aicowork audit` on git diffs; reports in the folder  | C02, C03                              |
| **Quarantine of untrusted content** before the agent reads it                               | none; injection handled (if at all) by the model vendor     | nonce markers, invisible-char stripping, phrase flags | C01                                   |
| **What can reach the model is written down and checked**                                    | implicit                                                    | `ai_surfaces` + reach report                          | C10                                   |
| **First-party-only trust boundary** (no plugins, no third-party skills, hash-locked kernel) | plugin/skill marketplaces with documented malware campaigns | manifest + anchor + skills lint                       | C11–C13                               |
| **Philosophy enforced by lint** (never delete, ≤ 5 signals, framework contract)             | conventions live in people's heads                          | conformance L2                                        | C12, C13                              |
| **Our code never touches the network**                                                      | telemetry by default is common                              | tested statically and dynamically                     | C20                                   |
| **Host-independent**                                                                        | tied to one app or vendor                                   | four-item host contract; host pages                   | `99_system/host-contract.md`          |

## The honest summary

If you want the best editor or the most integrations, use Obsidian or Notion. If you need your employer's compliance stack, use what your employer approved. AI-Cowork is for the person or small team who wants the agent to do real work on their files **and** wants to be able to show — to themselves, their team, or an auditor — what the agent could see, what it changed, and what left the machine. It pairs well with an editor: the folder is plain Markdown, so Obsidian or VS Code can open it; AI-Cowork only asks that their settings folders stay out of git and out of the agent's reach.
