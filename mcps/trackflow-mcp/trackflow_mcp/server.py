"""TrackFlow MCP server — Streamable HTTP on :8002 with MCP Auth (not FastMCP auth=)."""

from __future__ import annotations

import contextlib
import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from .auth import (
    bearer_verify_callable,
    build_mcp_auth,
    mint_local_access_token,
    protected_resource_metadata,
    resource_identifier,
)
from .scopes import AGENT_DEFAULT_SCOPES, SCOPES_SUPPORTED
from . import tools as tool_handlers

mcp = FastMCP(
    name="TrackFlow MCP",
    instructions=(
        "TrackFlow company tools for incidents (tickets) and read-only inventory. "
        "Requires OAuth Bearer JWT with scopes incidents:read|write and inventory:read."
    ),
    stateless_http=True,
)

# Shared MCP Auth instance. Tools read auth via mcp_auth.auth_info.
mcp_auth = build_mcp_auth()


def _json_result(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool(
    name="create_incident",
    description="Create a new TrackFlow incident ticket. Requires scope incidents:write.",
)
def create_incident(
    title: str,
    description: str,
    category: str,
    origin: str,
    branch: str,
    status: str = "open",
) -> str:
    return _json_result(
        tool_handlers.create_incident_tool(
            mcp_auth,
            title=title,
            description=description,
            category=category,
            origin=origin,
            branch=branch,
            status=status,
        )
    )


@mcp.tool(
    name="update_incident_status",
    description="Update an incident ticket status. Requires scope incidents:write.",
)
def update_incident_status(incident_id: int, status: str) -> str:
    return _json_result(
        tool_handlers.update_incident_status_tool(
            mcp_auth,
            incident_id=incident_id,
            status=status,
        )
    )


@mcp.tool(
    name="get_incident",
    description=(
        "Look up a single incident by numeric id or source_incident_id. "
        "Requires scope incidents:read."
    ),
)
def get_incident(
    incident_id: int | None = None,
    source_incident_id: str | None = None,
) -> str:
    return _json_result(
        tool_handlers.get_incident_tool(
            mcp_auth,
            incident_id=incident_id,
            source_incident_id=source_incident_id,
        )
    )


@mcp.tool(
    name="list_incidents",
    description="List incidents with optional filters. Requires scope incidents:read.",
)
def list_incidents(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> str:
    return _json_result(
        tool_handlers.list_incidents_tool(
            mcp_auth,
            status=status,
            origin=origin,
            branch=branch,
            category=category,
        )
    )


@mcp.tool(
    name="query_inventory",
    description=(
        "Query product stock by SKU and/or warehouse (read-only). "
        "Requires scope inventory:read. Inventory writes are never permitted."
    ),
)
def query_inventory(
    sku_code: str | None = None,
    warehouse: str | None = None,
) -> str:
    return _json_result(
        tool_handlers.query_inventory_tool(
            mcp_auth,
            sku_code=sku_code,
            warehouse=warehouse,
        )
    )


@mcp.tool(
    name="update_inventory_stock",
    description=(
        "Attempt to mutate inventory stock. Always rejected: inventory is read-only "
        "and inventory:write is never granted (insufficient_scope)."
    ),
)
def update_inventory_stock(sku_code: str, warehouse: str, quantity: int) -> str:
    return _json_result(
        tool_handlers.update_inventory_stock_tool(
            mcp_auth,
            sku_code=sku_code,
            warehouse=warehouse,
            quantity=quantity,
        )
    )


async def health(_request):
    return JSONResponse(
        {
            "status": "ok",
            "service": "trackflow-mcp",
            "auth": "mcp-auth",
            "resource": resource_identifier(),
            "scopes_supported": SCOPES_SUPPORTED,
        }
    )


async def protected_resource(_request):
    """RFC 9728 protected resource metadata (scopes for MCP clients)."""
    return JSONResponse(protected_resource_metadata())


async def mint_dev_token(request):
    """Dev-only helper to mint a local JWT (disabled when MCP_AUTH_MODE=oidc)."""
    if os.getenv("MCP_AUTH_MODE", "local").lower() == "oidc":
        return JSONResponse({"error": "disabled_in_oidc_mode"}, status_code=404)
    if os.getenv("MCP_AUTH_ALLOW_DEV_TOKEN", "0").strip() not in {"1", "true", "True"}:
        return JSONResponse({"error": "dev_token_disabled"}, status_code=403)
    body = {}
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
    scopes = body.get("scopes") or list(AGENT_DEFAULT_SCOPES)
    subject = body.get("subject") or "trackflow-agent"
    token = mint_local_access_token(subject=subject, scopes=list(scopes))
    return JSONResponse(
        {
            "access_token": token,
            "token_type": "Bearer",
            "scopes": scopes,
            "resource": resource_identifier(),
        }
    )


def create_app() -> Starlette:
    """Starlette app: MCP Auth metadata + bearer-protected MCP HTTP."""
    verify = bearer_verify_callable()
    bearer_kwargs: dict[str, Any] = {
        "audience": resource_identifier(),
        "show_error_details": os.getenv("MCP_AUTH_SHOW_ERROR_DETAILS", "").strip()
        in {"1", "true", "True"},
    }
    # No global required_scopes — each tool enforces its own scopes.
    bearer_mw = Middleware(
        mcp_auth.bearer_auth_middleware(verify, **bearer_kwargs)
    )

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/dev/token", mint_dev_token, methods=["POST", "GET"]),
            # MCP Auth authorization-server metadata
            mcp_auth.metadata_route(),
            # Protected resource metadata (RFC 9728) listing scopes_supported
            Route(
                "/.well-known/oauth-protected-resource",
                protected_resource,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-protected-resource/mcp",
                protected_resource,
                methods=["GET"],
            ),
            Mount("/", app=mcp.streamable_http_app(), middleware=[bearer_mw]),
        ],
        lifespan=lifespan,
    )


app = create_app()


def main() -> None:
    import uvicorn

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8002"))
    uvicorn.run(
        "trackflow_mcp.server:app",
        host=host,
        port=port,
        factory=False,
        reload=False,
    )


if __name__ == "__main__":
    main()
