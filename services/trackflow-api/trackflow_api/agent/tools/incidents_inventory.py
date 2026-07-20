"""Agent tools that call TrackFlow MCP (no direct incident/inventory service imports)."""

from __future__ import annotations

import re
from typing import Any

from ...core.config import get_settings
from .mcp_client import call_mcp_tool
from .timeout import ToolTimeoutError, call_with_timeout
from .types import (
    IncidentToolInput,
    InventoryToolInput,
    ToolResult,
    tool_fail,
    tool_ok,
)


def _timeout_seconds() -> float:
    return float(get_settings().agent_tool_timeout_seconds)


def extract_incident_ref(question: str) -> IncidentToolInput:
    text = question.strip()
    source_match = re.search(
        r"(?:ticket|incidencia|incident|source)[\s#:.-]*([A-Za-z0-9_-]+)",
        text,
        flags=re.IGNORECASE,
    )
    if source_match:
        token = source_match.group(1)
        if token.isdigit():
            return IncidentToolInput(incident_id=int(token), source_incident_id=None)
        return IncidentToolInput(incident_id=None, source_incident_id=token)

    bare_id = re.search(r"\b(\d{1,8})\b", text)
    if bare_id:
        return IncidentToolInput(incident_id=int(bare_id.group(1)), source_incident_id=None)
    return IncidentToolInput(incident_id=None, source_incident_id=None)


def extract_sku_and_warehouse(question: str) -> InventoryToolInput:
    text = question.strip()
    sku_match = re.search(r"\b([A-Z]{2,}[-_][A-Z0-9][-_A-Z0-9]*)\b", text, flags=re.IGNORECASE)
    warehouse = None
    if re.search(r"\b(LA|Los\s*Angeles)\b", text, flags=re.IGNORECASE):
        warehouse = "LA"
    elif re.search(r"\b(ZGZ|Zaragoza)\b", text, flags=re.IGNORECASE):
        warehouse = "ZGZ"
    return InventoryToolInput(
        sku_code=sku_match.group(1).upper() if sku_match else None,
        warehouse=warehouse,
    )


def lookup_incident_tool(question: str) -> dict[str, Any]:
    """Incident lookup via MCP `get_incident` (Bearer token + incidents:read)."""
    refs = extract_incident_ref(question)
    if refs.incident_id is None and not refs.source_incident_id:
        return tool_fail(
            "invalid_input",
            "No se pudo identificar un id de incidencia en la pregunta.",
        ).model_dump()

    arguments: dict[str, Any] = {}
    if refs.incident_id is not None:
        arguments["incident_id"] = refs.incident_id
    if refs.source_incident_id:
        arguments["source_incident_id"] = refs.source_incident_id

    try:
        result = call_with_timeout(
            call_mcp_tool,
            _timeout_seconds(),
            "get_incident",
            arguments,
        )
    except ToolTimeoutError as exc:
        return tool_fail(
            "timeout",
            "La consulta MCP al gestor de incidencias superó el tiempo límite.",
            detail=str(exc),
            incident_id=refs.incident_id,
            source_incident_id=refs.source_incident_id,
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return tool_fail(
            "service_unavailable",
            "El servidor MCP de incidencias no respondió.",
            detail=str(exc),
            incident_id=refs.incident_id,
            source_incident_id=refs.source_incident_id,
        ).model_dump()

    if result.get("error") in {"insufficient_scope", "unauthorized"}:
        return tool_fail(
            "insufficient_scope" if result.get("error") == "insufficient_scope" else "unauthorized",
            result.get("message") or "Permisos insuficientes para consultar incidencias.",
            detail=result.get("detail"),
            incident_id=refs.incident_id,
            source_incident_id=refs.source_incident_id,
        ).model_dump()

    if not result.get("ok") and not result.get("found"):
        err = result.get("error")
        if err and err not in {"not_found"}:
            return tool_fail(
                "service_unavailable",
                result.get("message") or "Error al consultar incidencias vía MCP.",
                detail=str(err),
                incident_id=refs.incident_id,
                source_incident_id=refs.source_incident_id,
            ).model_dump()
        return tool_fail(
            "not_found",
            "No se encontró la incidencia solicitada en el gestor.",
            incident_id=refs.incident_id,
            source_incident_id=refs.source_incident_id,
        ).model_dump()

    return tool_ok(result).model_dump()


def lookup_inventory_tool(question: str) -> dict[str, Any]:
    """Inventory lookup via MCP `query_inventory` (Bearer token + inventory:read)."""
    refs = extract_sku_and_warehouse(question)
    arguments: dict[str, Any] = {}
    if refs.sku_code:
        arguments["sku_code"] = refs.sku_code
    if refs.warehouse:
        arguments["warehouse"] = refs.warehouse

    try:
        result = call_with_timeout(
            call_mcp_tool,
            _timeout_seconds(),
            "query_inventory",
            arguments,
        )
    except ToolTimeoutError as exc:
        return tool_fail(
            "timeout",
            "La consulta MCP al inventario superó el tiempo límite.",
            detail=str(exc),
            sku=refs.sku_code,
            warehouse=refs.warehouse,
        ).model_dump()
    except Exception as exc:  # noqa: BLE001
        return tool_fail(
            "service_unavailable",
            "El servidor MCP de inventario no respondió.",
            detail=str(exc),
            sku=refs.sku_code,
            warehouse=refs.warehouse,
        ).model_dump()

    if not result.get("ok") and not result.get("found"):
        err = result.get("error")
        if err and err not in {"not_found"}:
            return tool_fail(
                "service_unavailable",
                result.get("message") or "Error al consultar inventario vía MCP.",
                detail=str(err),
                sku=refs.sku_code,
                warehouse=refs.warehouse,
            ).model_dump()
        return tool_fail(
            "not_found",
            "No se encontró stock para el SKU/almacén consultado.",
            sku=refs.sku_code,
            warehouse=refs.warehouse,
        ).model_dump()

    return tool_ok(result).model_dump()


def parse_tool_result(payload: dict[str, Any] | ToolResult) -> ToolResult:
    if isinstance(payload, ToolResult):
        return payload
    return ToolResult.model_validate(payload)
