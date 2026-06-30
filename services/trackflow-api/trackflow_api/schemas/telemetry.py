"""
Schemas de validación para el endpoint de telemetría.

Basados en el plan de telemetría Fase 1 (docs/telemetry/event-schemas.json).
Este stub valida el envelope y la whitelist de payload sin persistir.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProcessingMode(str, Enum):
    STREAM = "stream"
    BATCH = "batch"


class Source(str, Enum):
    TRACKFLOW_API = "trackflow-api"
    BACKOFFICE_WEB = "backoffice-web"


class EventName(str, Enum):
    RECEIVING_ORDER_CREATED = "receiving_order_created"
    DISPATCH_ORDER_CREATED = "dispatch_order_created"
    STOCK_THRESHOLD_TRIGGERED = "stock_threshold_triggered"
    DIRECT_STOCK_EDIT_REJECTED = "direct_stock_edit_rejected"
    DISPATCH_ORDER_FAILED = "dispatch_order_failed"
    RECEIVING_ORDER_FAILED = "receiving_order_failed"
    USER_LOGIN_FAILED = "user_login_failed"
    DISPATCH_FORM_ABANDONED = "dispatch_form_abandoned"
    INBOUND_ORDER_SUBMITTED = "inbound_order_submitted"
    OUTBOUND_ORDER_SUBMITTED = "outbound_order_submitted"


# Whitelist de propiedades permitidas en payload por event_name
ALLOWED_PAYLOAD_PROPERTIES: dict[EventName, set[str]] = {
    EventName.RECEIVING_ORDER_CREATED: {
        "receiving_order_id", "sku_id", "sku_code", "client_id",
        "warehouse", "quantity", "carrier", "created_by", "created_at",
    },
    EventName.DISPATCH_ORDER_CREATED: {
        "dispatch_order_id", "sku_id", "sku_code", "client_id",
        "warehouse", "quantity", "destination_country", "carrier",
        "created_by", "created_at", "stock_after_dispatch",
    },
    EventName.STOCK_THRESHOLD_TRIGGERED: {
        "sku_id", "sku_code", "client_id", "warehouse",
        "current_stock", "min_stock_threshold",
        "triggered_by_dispatch_order_id", "category",
    },
    EventName.DIRECT_STOCK_EDIT_REJECTED: {
        "sku_id", "sku_code", "client_id", "warehouse",
        "attempted_stock_value", "current_stock", "requested_by",
        "http_status", "rejection_reason",
    },
    EventName.DISPATCH_ORDER_FAILED: {
        "sku_id", "sku_code", "client_id", "warehouse",
        "requested_quantity", "available_stock", "destination_country",
        "failure_reason", "is_peak_hours", "requested_by",
    },
    EventName.RECEIVING_ORDER_FAILED: {
        "sku_id", "client_id", "warehouse", "requested_quantity",
        "failure_reason", "requested_by",
    },
    EventName.USER_LOGIN_FAILED: {
        "failure_reason", "source_ip_hash",
    },
    EventName.DISPATCH_FORM_ABANDONED: {
        "warehouse", "sku_id", "form_session_id",
        "seconds_on_form", "abandon_reason",
    },
    EventName.INBOUND_ORDER_SUBMITTED: {
        "sku_id", "quantity", "warehouse", "reference",
    },
    EventName.OUTBOUND_ORDER_SUBMITTED: {
        "sku_id", "quantity", "warehouse", "exit_type", "tracking_number",
    },
}


class TelemetryEventPayload(BaseModel):
    """Payload específico del evento. Se valida contra whitelist por event_name."""

    pass


class TelemetryEvent(BaseModel):
    """Envelope común de un evento de telemetría."""

    event_id: str = Field(..., description="UUID v4")
    event_name: EventName
    event_version: str = Field(..., pattern=r"^\d+\.\d+$")
    occurred_at: str = Field(..., description="ISO-8601 UTC")
    source: Source
    warehouse: str | None = None
    correlation_id: str | None = None
    processing_mode: ProcessingMode
    payload: dict[str, Any]

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 timestamp: {v}") from exc
        return v

    @field_validator("payload")
    @classmethod
    def validate_payload_whitelist(cls, v: dict[str, Any], info) -> dict[str, Any]:
        """Rechaza claves en payload que no estén en la whitelist del event_name."""
        if not info.data or "event_name" not in info.data:
            return v

        event_name = info.data["event_name"]
        allowed = ALLOWED_PAYLOAD_PROPERTIES.get(event_name, set())

        extra_keys = set(v.keys()) - allowed
        if extra_keys:
            raise ValueError(
                f"Payload keys not allowed for '{event_name.value}': {sorted(extra_keys)}"
            )

        return v


class TelemetryBatchRequest(BaseModel):
    """Lote de eventos recibido en una sola petición."""

    events: list[TelemetryEvent]