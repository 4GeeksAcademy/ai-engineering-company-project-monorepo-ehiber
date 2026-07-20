# mcps folder

This folder contains Model Context Protocol servers and related documentation used by the company tooling and agents.

## TrackFlow MCP (Variant B — MCP Auth)

Server package: [`trackflow-mcp/`](./trackflow-mcp/)

| Item | Value |
|------|--------|
| Transport | Streamable HTTP |
| Port | **8002** |
| Auth | **[MCP Auth](https://mcp-auth.dev/)** (`mcpauth`) — protected resource metadata + Bearer JWT |
| Scopes | `incidents:read`, `incidents:write`, `inventory:read` (never `inventory:write`) |

### Tools

| Tool | Scope | Notes |
|------|-------|--------|
| `create_incident` | `incidents:write` | Creates a ticket via `incident_manager_service` |
| `update_incident_status` | `incidents:write` | Status transition rules enforced by existing service |
| `get_incident` | `incidents:read` | Lookup by id or `source_incident_id` |
| `list_incidents` | `incidents:read` | Optional filters |
| `query_inventory` | `inventory:read` | Read-only stock lookup |
| `update_inventory_stock` | — | **Always rejected** (`insufficient_scope`) — inventory is read-only |

### How to obtain a token

**Local / Docker (default `MCP_AUTH_MODE=local`):**

1. Start the server (`uvicorn` or `docker compose up trackflow-mcp`).
2. Mint a JWT:

```bash
curl -s -X POST http://localhost:8002/dev/token \
  -H 'Content-Type: application/json' \
  -d '{"scopes":["incidents:read","incidents:write","inventory:read"]}'
```

Or set `TRACKFLOW_MCP_TOKEN` in `.env` after minting. The knowledge agent can also mint a token with `MCP_AUTH_JWT_SECRET` when `TRACKFLOW_MCP_TOKEN` is empty.

**OIDC provider (`MCP_AUTH_MODE=oidc`):**

1. Set `MCP_AUTH_ISSUER` to your OIDC issuer URL.
2. MCP Auth fetches provider metadata and validates JWTs via JWKS (`bearer_auth_middleware("jwt")`).
3. Request an access token from your IdP with audience = `MCP_AUTH_RESOURCE` (default `http://localhost:8002/mcp`) and the scopes above.
4. Call MCP with `Authorization: Bearer <access_token>`.

Protected resource metadata (RFC 9728) is at `/.well-known/oauth-protected-resource` (lists `scopes_supported`). MCP Auth also exposes authorization-server metadata at `/.well-known/oauth-authorization-server`.

### Run locally

```bash
# from monorepo root, with PYTHONPATH including services/trackflow-api
cd mcps/trackflow-mcp
pip install -e .
export PYTHONPATH=../../services/trackflow-api:../..
export MCP_AUTH_MODE=local
export MCP_AUTH_JWT_SECRET=trackflow-mcp-dev-secret-change-me
uvicorn trackflow_mcp.server:app --host 0.0.0.0 --port 8002
```

Or via Compose:

```bash
docker compose up trackflow-mcp
```

Health: `GET http://localhost:8002/health`

MCP endpoint: `http://localhost:8002/mcp` (Bearer required)

### Agent integration

The LangGraph knowledge agent connects with `langchain-mcp-adapters` `MultiServerMCPClient` to `TRACKFLOW_MCP_URL` (default `http://localhost:8002/mcp`) and does **not** call `incident_manager_service` / `inventory_query_service` from tool nodes — those services are only used inside this MCP server.
