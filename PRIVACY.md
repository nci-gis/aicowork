# Privacy — AI-Cowork 0.0.1

**The reference tools collect nothing and send nothing.** No telemetry, no update checks, no crash reports, no analytics, no CDN. The viewer listens on 127.0.0.1 only and serves only its own vendored files. This is tested: `98_tools/tests/test_nonet.py` fails if any tool module imports a network library (the viewer's loopback server excepted) or if the commands try a non-loopback connection or a DNS lookup.

**The agent host is a different matter.** Whatever host you connect the folder to (an agent app, an IDE assistant) sends the files it opens to its model provider under that provider's terms. The kernel cannot see or stop this. Treat the connected folder as _sent to the model_ (CONVENTIONS "Reach"), list the approved hosts in `policy.yaml` → `ai_surfaces`, and check the host's own telemetry and retention settings (for Claude Cowork: `hosts/claude-cowork-hardening.md`). Verify the host's current telemetry switches in its own documentation before relying on them — they change between releases.

**Your data is yours.** Nothing in the kernel or the tools uploads, syncs or shares it. Backups and exports happen only through `aicowork backup` / `aicowork export` to destinations you listed in `policy.yaml`, and each one leaves a receipt in `06_logs/egress/`.
