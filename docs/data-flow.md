# Data flow — where content goes

```
                      ┌──────────────────────────── the owner's machine ────────────────────────────┐
  mail, web, notes    │                                                                             │
 ─────────────────────┼─▶ 00_inbox/  ──ingest──▶ quarantined text ──┐                               │
   (untrusted)        │                                             │                               │
                      │   connected folder (plain files, git)       │                               │
                      │   ┌───────────────────────────────────┐     ▼                               │
                      │   │ 01_…09_ notes · INDEX · policy     │◀── agent host (reads/writes files) ─┼──▶ MODEL PROVIDER
                      │   │ 99_system/ kernel · 98_tools/      │         │                           │    (the named egress:
                      │   └───────────────────────────────────┘         │ scheduled prompts          │     everything the host
                      │        │            │            │               │                           │     opens is sent)
                      │        │ viewer     │ backup     │ export        ▼                           │
                      │        ▼ (127.0.0.1)▼ (bundle)   ▼ (gate)   06_logs/audit/  (host-side audit) │
                      │    browser tab   policy-listed  policy-listed                               │
                      │                  destination    destination ──▶ 06_logs/egress/ receipts     │
                      │                                                  (hash-chained)              │
                      │   anchor: commit + manifest hashes ──▶ user profile (outside the folder)     │
                      └─────────────────────────────────────────────────────────────────────────────┘
```

| Flow                           | Leaves the machine?                                                                                                | Controlled by                                                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Agent host → model provider    | **yes — always, for what the host opens**                                                                          | the host and the organisation (hardening guide); the kernel lists approved surfaces in `policy.yaml` and reports reach |
| Viewer ↔ browser               | no (loopback only, enforced)                                                                                       | viewer guard                                                                                                           |
| `backup`                       | only to a destination listed in `policy.yaml`                                                                      | policy + receipt                                                                                                       |
| `export`                       | only to a destination listed in `policy.yaml`, only files at or below its `accepts` level, private blocks stripped | policy + receipt                                                                                                       |
| `git push`                     | only to remotes listed in `policy.yaml`                                                                            | pre-push hook                                                                                                          |
| Tools (CLI, viewer) → internet | never                                                                                                              | tested (`test_nonet.py`)                                                                                               |
