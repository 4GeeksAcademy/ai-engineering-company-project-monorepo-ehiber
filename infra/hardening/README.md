# Infra hardening snippets

Templates for a TrackFlow host (VPS or VM). They are **not** applied automatically. Local development uses Docker Compose; see [docs/cibersecurity/HARDENING.md](../docs/cibersecurity/HARDENING.md).

| File | Purpose |
| --- | --- |
| `sshd/sshd_config.d-trackflow.conf` | Disable direct root SSH; allow `deploy` only |
| `ufw/trackflow.rules.sh` | Firewall: 22/80/443 only (plus optional loopback notes) |
| `permissions/layout.md` | Separate code, logs, and secrets on disk |
