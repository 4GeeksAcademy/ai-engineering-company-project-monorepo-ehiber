"""Shared fixtures for telemetry pipeline tests (no Prefect required)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine

PIPELINE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE_ROOT.parents[1]
SERVICES_API = REPO_ROOT / "services" / "trackflow-api"
SERVICES = REPO_ROOT / "services"

for path in (str(PIPELINE_ROOT), str(SERVICES_API), str(SERVICES)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture()
def pipeline_env(tmp_path, monkeypatch):
    db_path = tmp_path / "pipeline.db"
    uri = f"sqlite:///{db_path}"
    monkeypatch.setenv("SUPABASE_URI", uri)

    from trackflow_api.core import config as config_module
    from trackflow_api.core import database as database_module
    from trackflow_api import models  # noqa: F401

    config_module.get_settings.cache_clear()
    database_module.get_inventory_engine.cache_clear()

    engine = create_engine(uri, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def insert_telemetry_event(
    engine,
    *,
    event_type: str,
    occurred_at: datetime,
    warehouse: str,
    payload: dict,
    processing_mode: str = "batch",
) -> None:
    from trackflow_api.models import TelemetryEvent

    with Session(engine) as session:
        session.add(
            TelemetryEvent(
                event_id=str(uuid4()),
                event_type=event_type,
                timestamp=occurred_at,
                source="trackflow-api",
                tags={"warehouse": warehouse},
                payload={**payload, "warehouse": warehouse},
                processing_mode=processing_mode,
            )
        )
        session.commit()


def seed_fulfillment_scenario(engine, *, day: datetime) -> None:
    wh = "los_angeles"
    insert_telemetry_event(
        engine,
        event_type="dispatch_order_created",
        occurred_at=day.replace(hour=10),
        warehouse=wh,
        payload={
            "dispatch_order_id": 1,
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "quantity": 5,
            "destination_country": "US",
            "carrier": "FedEx",
            "created_by": str(uuid4()),
            "created_at": day.replace(hour=10).isoformat().replace("+00:00", "Z"),
            "stock_after_dispatch": 20,
        },
    )
    insert_telemetry_event(
        engine,
        event_type="dispatch_order_created",
        occurred_at=day.replace(hour=10, minute=30),
        warehouse=wh,
        payload={
            "dispatch_order_id": 2,
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "quantity": 3,
            "destination_country": "US",
            "carrier": "FedEx",
            "created_by": str(uuid4()),
            "created_at": day.replace(hour=10, minute=30).isoformat().replace("+00:00", "Z"),
            "stock_after_dispatch": 15,
        },
    )
    insert_telemetry_event(
        engine,
        event_type="dispatch_order_failed",
        occurred_at=day.replace(hour=11),
        warehouse=wh,
        payload={
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "requested_quantity": 50,
            "available_stock": 12,
            "destination_country": "US",
            "failure_reason": "insufficient_stock",
            "is_peak_hours": False,
            "requested_by": str(uuid4()),
        },
        processing_mode="stream",
    )
    insert_telemetry_event(
        engine,
        event_type="dispatch_order_failed",
        occurred_at=day.replace(hour=11, minute=30),
        warehouse=wh,
        payload={
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "requested_quantity": 5,
            "available_stock": 12,
            "destination_country": "US",
            "failure_reason": "sku_not_found",
            "is_peak_hours": False,
            "requested_by": str(uuid4()),
        },
        processing_mode="stream",
    )


def seed_discrepancy_scenario(engine, *, day: datetime) -> None:
    insert_telemetry_event(
        engine,
        event_type="direct_stock_edit_rejected",
        occurred_at=day.replace(hour=9),
        warehouse="zaragoza",
        payload={
            "sku_id": 3,
            "sku_code": "TF-FASH-0003",
            "client_id": str(uuid4()),
            "attempted_stock_value": 999,
            "current_stock": 40,
            "requested_by": str(uuid4()),
            "http_status": 409,
            "rejection_reason": "direct_stock_edit_forbidden",
        },
        processing_mode="stream",
    )


def seed_cycle_time_scenario(engine, *, day: datetime) -> None:
    wh = "los_angeles"
    insert_telemetry_event(
        engine,
        event_type="receiving_order_created",
        occurred_at=day.replace(hour=8),
        warehouse=wh,
        payload={
            "receiving_order_id": 100,
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "quantity": 20,
            "carrier": "DHL",
            "created_by": str(uuid4()),
            "created_at": day.replace(hour=8).isoformat().replace("+00:00", "Z"),
        },
    )
    insert_telemetry_event(
        engine,
        event_type="dispatch_order_created",
        occurred_at=day.replace(hour=14),
        warehouse=wh,
        payload={
            "dispatch_order_id": 50,
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "quantity": 5,
            "destination_country": "US",
            "carrier": "FedEx",
            "created_by": str(uuid4()),
            "created_at": day.replace(hour=14).isoformat().replace("+00:00", "Z"),
            "stock_after_dispatch": 15,
        },
    )
