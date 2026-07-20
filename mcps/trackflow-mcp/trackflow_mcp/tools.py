"""MCP tool handlers that reuse trackflow_api services (no duplicated business logic)."""

from __future__ import annotations

from typing import Any

from . import path_setup  # noqa: F401

from fastapi import HTTPException
from mcpauth import MCPAuth
from mcpauth.exceptions import BearerAuthExceptionCode, MCPAuthBearerAuthException

from trackflow_api.schemas.incidents_manager import IncidentCreate, IncidentStatusUpdate
from trackflow_api.services import incident_manager_service
from trackflow_api.services import inventory_query_service

from .auth import require_scopes
from .scopes import (
    SCOPE_INCIDENTS_READ,
    SCOPE_INCIDENTS_WRITE,
    SCOPE_INVENTORY_READ,
    SCOPE_INVENTORY_WRITE,
)


def _public_incident(incident) -> dict[str, Any]:
    if hasattr(incident, "model_dump"):
        return incident.model_dump(mode="json")
    return dict(incident)


def create_incident_tool(
    mcp_auth: MCPAuth,
    *,
    title: str,
    description: str,
    category: str,
    origin: str,
    branch: str,
    status: str = "open",
) -> dict[str, Any]:
    require_scopes(mcp_auth, SCOPE_INCIDENTS_WRITE)
    try:
        created = incident_manager_service.create_incident(
            IncidentCreate(
                title=title,
                description=description,
                category=category,
                origin=origin,
                branch=branch,
                status=status,
            )
        )
    except incident_manager_service.FieldValidationError as exc:
        return {"ok": False, "error": "validation_error", "field": exc.field, "message": exc.message}
    except HTTPException as exc:
        return {"ok": False, "error": "http_error", "status_code": exc.status_code, "detail": exc.detail}
    return {"ok": True, "incident": _public_incident(created)}


def update_incident_status_tool(
    mcp_auth: MCPAuth,
    *,
    incident_id: int,
    status: str,
) -> dict[str, Any]:
    require_scopes(mcp_auth, SCOPE_INCIDENTS_WRITE)
    try:
        updated = incident_manager_service.update_incident_status(
            incident_id,
            IncidentStatusUpdate(status=status),
        )
    except incident_manager_service.FieldValidationError as exc:
        return {"ok": False, "error": "validation_error", "field": exc.field, "message": exc.message}
    except HTTPException as exc:
        return {"ok": False, "error": "http_error", "status_code": exc.status_code, "detail": exc.detail}
    return {"ok": True, "incident": _public_incident(updated)}


def get_incident_tool(
    mcp_auth: MCPAuth,
    *,
    incident_id: int | None = None,
    source_incident_id: str | None = None,
) -> dict[str, Any]:
    require_scopes(mcp_auth, SCOPE_INCIDENTS_READ)
    result = incident_manager_service.lookup_incident(
        incident_id=incident_id,
        source_incident_id=source_incident_id,
    )
    return {"ok": bool(result.get("found")), **result}


def list_incidents_tool(
    mcp_auth: MCPAuth,
    *,
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    require_scopes(mcp_auth, SCOPE_INCIDENTS_READ)
    try:
        items = incident_manager_service.list_incidents(
            status=status,
            origin=origin,
            branch=branch,
            category=category,
        )
    except incident_manager_service.FieldValidationError as exc:
        return {"ok": False, "error": "validation_error", "field": exc.field, "message": exc.message}
    return {
        "ok": True,
        "incidents": [_public_incident(item) for item in items],
        "count": len(items),
    }


def query_inventory_tool(
    mcp_auth: MCPAuth,
    *,
    sku_code: str | None = None,
    warehouse: str | None = None,
) -> dict[str, Any]:
    require_scopes(mcp_auth, SCOPE_INVENTORY_READ)
    result = inventory_query_service.lookup_stock(sku_code=sku_code, warehouse=warehouse)
    return {"ok": bool(result.get("found")), **result}


def update_inventory_stock_tool(
    mcp_auth: MCPAuth,
    *,
    sku_code: str,
    warehouse: str,
    quantity: int,
) -> dict[str, Any]:
    """Explicitly reject inventory writes — inventory is read-only; never grant inventory:write."""
    # Always deny, even if a token somehow carries inventory:write.
    auth_info = mcp_auth.auth_info
    if auth_info is None:
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_BEARER_TOKEN)
    if SCOPE_INVENTORY_WRITE in (auth_info.scopes or []):
        # Still reject — write capability is not part of the product contract.
        raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES)
    raise MCPAuthBearerAuthException(BearerAuthExceptionCode.MISSING_REQUIRED_SCOPES)
