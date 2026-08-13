"""MCP Auth tests: bearer required, scope enforcement, inventory write rejection."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Monorepo imports for trackflow_api services used by tool handlers
REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = REPO_ROOT / "services" / "trackflow-api"
MCP_ROOT = Path(__file__).resolve().parents[1]
for path in (REPO_ROOT, API_ROOT, MCP_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

os.environ.setdefault("MCP_AUTH_MODE", "local")
os.environ.setdefault("MCP_AUTH_JWT_SECRET", "test-secret-mcp-auth-32bytes-min!!")
os.environ.setdefault("MCP_AUTH_ISSUER", "http://localhost:8002/oidc")
os.environ.setdefault("MCP_AUTH_RESOURCE", "http://localhost:8002/mcp")
os.environ.setdefault("SUPABASE_URI", "sqlite:////tmp/trackflow-mcp-test.db")


@pytest.fixture()
def auth_env(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_MODE", "local")
    monkeypatch.setenv("MCP_AUTH_JWT_SECRET", "test-secret-mcp-auth-32bytes-min!!")
    monkeypatch.setenv("MCP_AUTH_ISSUER", "http://localhost:8002/oidc")
    monkeypatch.setenv("MCP_AUTH_RESOURCE", "http://localhost:8002/mcp")


def test_local_jwt_roundtrip(auth_env):
    from trackflow_mcp.auth import mint_local_access_token, verify_local_jwt

    token = mint_local_access_token(scopes=["incidents:read", "inventory:read"])
    info = verify_local_jwt(token)
    assert info.subject
    assert "incidents:read" in info.scopes
    assert "inventory:read" in info.scopes


def test_invalid_token_rejected(auth_env):
    from mcpauth.exceptions import MCPAuthTokenVerificationException

    from trackflow_mcp.auth import verify_local_jwt

    with pytest.raises(MCPAuthTokenVerificationException):
        verify_local_jwt("not-a-jwt")


def test_mcp_http_requires_auth(auth_env):
    from starlette.testclient import TestClient

    from trackflow_mcp.server import create_app

    client = TestClient(create_app())
    # Unauthenticated MCP traffic must fail closed
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert response.status_code in {401, 403}


def test_health_is_public(auth_env):
    from starlette.testclient import TestClient

    from trackflow_mcp.server import create_app

    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["auth"] == "mcp-auth"
    assert "incidents:read" in body["scopes_supported"]
    assert "inventory:write" not in body["scopes_supported"]


def test_protected_resource_metadata_lists_scopes(auth_env):
    from starlette.testclient import TestClient

    from trackflow_mcp.server import create_app

    client = TestClient(create_app())
    # MCP Auth may mount metadata at several well-known paths
    paths = [
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
    ]
    responses = [client.get(path) for path in paths]
    ok = [r for r in responses if r.status_code == 200]
    assert ok, f"no metadata route succeeded: {[r.status_code for r in responses]}"
    payload = ok[0].json()
    scopes = payload.get("scopes_supported") or payload.get("scopesSupported") or []
    assert "incidents:read" in scopes
    assert "inventory:read" in scopes
    assert "inventory:write" not in scopes


class _FakeAuth:
    def __init__(self, scopes: list[str]):
        from mcpauth.types import AuthInfo

        self._info = AuthInfo(
            token="x",
            issuer="http://localhost:8002/oidc",
            subject="tester",
            scopes=scopes,
            claims={},
        )

    @property
    def auth_info(self):
        return self._info


def test_scope_enforcement_on_incident_read(auth_env):
    from mcpauth.exceptions import MCPAuthBearerAuthException

    from trackflow_mcp import tools as tool_handlers
    from trackflow_mcp.scopes import SCOPE_INVENTORY_READ

    # Token with only inventory:read must not call incidents:read tools
    with pytest.raises(MCPAuthBearerAuthException):
        tool_handlers.get_incident_tool(_FakeAuth([SCOPE_INVENTORY_READ]), incident_id=1)


def test_inventory_write_always_rejected(auth_env):
    from mcpauth.exceptions import MCPAuthBearerAuthException

    from trackflow_mcp import tools as tool_handlers
    from trackflow_mcp.scopes import SCOPE_INVENTORY_READ, SCOPE_INVENTORY_WRITE

    # Even with inventory:write in the token, writes are rejected by design
    with pytest.raises(MCPAuthBearerAuthException):
        tool_handlers.update_inventory_stock_tool(
            _FakeAuth([SCOPE_INVENTORY_READ, SCOPE_INVENTORY_WRITE]),
            sku_code="TF-ELEC-0010",
            warehouse="LA",
            quantity=99,
        )


def test_dev_token_endpoint(auth_env, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_ALLOW_DEV_TOKEN", "1")
    from starlette.testclient import TestClient

    from trackflow_mcp.auth import verify_local_jwt
    from trackflow_mcp.server import create_app

    client = TestClient(create_app())
    response = client.post("/dev/token", json={"scopes": ["incidents:read"]})
    assert response.status_code == 200
    token = response.json()["access_token"]
    info = verify_local_jwt(token)
    assert info.scopes == ["incidents:read"]


def test_dev_token_disabled_by_default(auth_env, monkeypatch):
    monkeypatch.setenv("MCP_AUTH_ALLOW_DEV_TOKEN", "0")
    from starlette.testclient import TestClient

    from trackflow_mcp.server import create_app

    client = TestClient(create_app())
    response = client.post("/dev/token", json={"scopes": ["incidents:read"]})
    assert response.status_code == 403
