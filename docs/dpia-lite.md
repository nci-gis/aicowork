# DPIA-lite — personal data in an AI-Cowork instance (template)

_A starting point for the owner's own assessment, not legal advice. Copy this file into your instance (`09_decisions/` is a good place), fill every `<…>`, and take the items marked **unverified** to counsel. The example at the end shows one owner's filled-in §0 and §4; it is not yours._

## 0. Your inputs

| Input                                                                             | Yours |
| --------------------------------------------------------------------------------- | ----- |
| Jurisdiction(s) whose data-protection law applies to you                          | <…>   |
| Whether the folder holds work data, personal data, or both                        | <…>   |
| The AI host(s) you connect, and who approved each (`policy.yaml` → `ai_surfaces`) | <…>   |
| Where the model provider processes data (country), from its terms                 | <…>   |
| Your organisation's process for reporting a breach, if the folder holds work      | <…>   |
| Date of this assessment, and when you will review it                              | <…>   |

## 1. What personal data an instance holds

- the owner's identity and roles (`03_personas/me.md`);
- other people: personas, mail summaries, meeting notes (colleagues, clients, family);
- possibly sensitive categories: health (the `health` circle), family matters, location, finances.

## 2. Where it is processed

- on the owner's machine (files, git, local tools);
- **by the agent host's model provider**, for every file the host opens (the named egress — `docs/data-flow.md`);
- at backup/export destinations listed in `policy.yaml`.

## 3. Risks and mitigations

| Risk                                          | Mitigation in AI-Cowork                        | Owner's action                                                               |
| --------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------- |
| Third parties' data sent to a model provider  | reach report; `ai_surfaces` in the policy      | use only approved hosts; keep what must not reach a model outside the folder |
| Excessive retention                           | `expires` / `review_by` + `aicowork retention` | set review dates on people-heavy notes                                       |
| Erasure request vs. never-delete              | human-only `purge` with a hash-only tombstone  | rotate old backups; note that git history keeps content until rewritten      |
| Cross-border transfer (model provider abroad) | the policy records approved surfaces           | **unverified**: whether a transfer-impact assessment is needed for your case |
| Breach (lost laptop, leaked backup)           | backups only to listed destinations; receipts  | device encryption; report per your organisation's process                    |

## 4. Open questions for counsel (unverified)

Write yours; the shape of each is "does `<rule of my jurisdiction>` apply to `<this part of the setup>`?":

- Does purely personal or household processing fall outside <your jurisdiction's law> in this setup?
- What deletion timelines does <your jurisdiction's law> set, and can a folder that never deletes (archive + git history) meet them?
- Whether an employer's approval of an AI host covers personal-circle data in the same folder.
- <…>

## Example — one owner's §0 and §4 (secondary sources, researched 2026-10-01; verify before relying on it)

§0: jurisdictions Vietnam and Japan; the folder holds both work and personal data; host approved by the employer's IT. References found: Vietnam Personal Data Protection Law 91/2025/QH15 and Decree 356/2025/ND-CP (effective 2026-01-01); Japan APPI; METI/MIC AI Guidelines for Business v1.1 (soft law).

§4: does personal or household processing fall outside the Vietnam PDP Law here? Deletion timelines under Decree 356/2025 (sources disagree). Whether an employer's approval of an AI host covers personal-circle data in the same folder.
