"""OAuth scopes for TrackFlow MCP tools (least privilege; no inventory:write)."""

from __future__ import annotations

SCOPE_INCIDENTS_READ = "incidents:read"
SCOPE_INCIDENTS_WRITE = "incidents:write"
SCOPE_INVENTORY_READ = "inventory:read"
# Intentionally never granted — inventory is read-only by design.
SCOPE_INVENTORY_WRITE = "inventory:write"

SCOPES_SUPPORTED: list[str] = [
    SCOPE_INCIDENTS_READ,
    SCOPE_INCIDENTS_WRITE,
    SCOPE_INVENTORY_READ,
]

AGENT_DEFAULT_SCOPES: list[str] = [
    SCOPE_INCIDENTS_READ,
    SCOPE_INCIDENTS_WRITE,
    SCOPE_INVENTORY_READ,
]
