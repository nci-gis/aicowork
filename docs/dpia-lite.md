# DPIA-lite — personal data in an AI-Cowork instance

_A starting point for the owner's own assessment, not legal advice. Items marked **unverified** need counsel. Regulatory references from research on 2026-10-01 (secondary sources): Vietnam Personal Data Protection Law 91/2025/QH15 and Decree 356/2025/ND-CP (effective 2026-01-01); Japan APPI; METI/MIC AI Guidelines for Business v1.1 (soft law)._

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

- Does purely personal or household processing fall outside the Vietnam PDP Law in this setup?
- Deletion timelines under Decree 356/2025 (sources disagree).
- Whether an employer's approval of an AI host covers personal-circle data in the same folder.
