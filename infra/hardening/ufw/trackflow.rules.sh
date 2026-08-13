#!/usr/bin/env bash
# Baseline UFW for a TrackFlow edge host. Review before running.
# Public: SSH + HTTPS (and HTTP only for ACME/redirect).
set -euo pipefail

ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# Do not publish Redis, Qdrant, MCP, Flower, or Postgres on this host.
ufw --force enable
ufw status verbose
