"""Typed input/output contracts for knowledge-agent live tools."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class IncidentToolInput(BaseModel):
    incident_id: int | None = None
    source_incident_id: str | None = None


class InventoryToolInput(BaseModel):
    sku_code: str | None = None
    warehouse: str | None = None


class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    message: str | None = None
    detail: str | None = None
    incident_id: int | None = None
    source_incident_id: str | None = None
    sku: str | None = None
    warehouse: str | None = None


ToolErrorCode = Literal[
    "not_found",
    "service_unavailable",
    "timeout",
    "invalid_input",
    "insufficient_scope",
    "unauthorized",
]


def tool_ok(data: dict[str, Any]) -> ToolResult:
    return ToolResult(ok=True, data=data, error=None)


def tool_fail(
    code: ToolErrorCode,
    message: str,
    *,
    detail: str | None = None,
    **extra: Any,
) -> ToolResult:
    return ToolResult(
        ok=False,
        data=None,
        error=code,
        message=message,
        detail=detail,
        **{k: v for k, v in extra.items() if k in ToolResult.model_fields},
    )
