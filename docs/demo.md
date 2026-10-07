# Demo — "a malicious mail arrives" (10 minutes)

_Shows the whole detect-and-prove loop on the fictional example instance. Needs the tools and any agent host._

```
# 1. a fresh copy of the example instance, checked against this kernel
aicowork init /tmp/demo --preset personal-simple
cp -r 99_system/conformance/fixtures/example-instance/* /tmp/demo/
cd /tmp/demo && git add -A && git commit -qm start && START=$(git rev-parse HEAD)
aicowork conform                      # PASS

# 2. the attack: three red-team mails land in the inbox
cp 99_system/conformance/fixtures/redteam/0{2,4,6}_*.txt 00_inbox/
aicowork ingest                       # wrapped in <<UNTRUSTED>>, suspicious phrases listed

# 3. the agent triages (in the host, manual-approval mode): "triage my inbox"

# 4. the proof, host-side
aicowork audit --since $START --task triage     # CLEAN, or FLAGGED with the exact file
aicowork conform --case L3-REDTEAM --since $START
aicowork reach                                  # what the model could see
aicowork export --dest share-public --dry-run   # what would leave, and why the rest would not
```

What to point at:

1. `ingest` output — the "raise visibility", "edit policy" and "curl" lines are flagged before the agent ever reads them.
2. `audit` — if the agent had edited `policy.yaml` or raised a visibility, it would be named here, file by file.
3. `export --dry-run` — `09_decisions/…pilot…` is `internal` and the destination accepts only `public`, so it stays; the private block inside it would be stripped anyway.
4. `06_logs/audit/` and `06_logs/egress/` — the evidence is plain text in the folder.
