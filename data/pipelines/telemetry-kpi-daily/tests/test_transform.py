"""Unit tests for transformation stage (A: stage fn + C: analysis.py) — no Prefect."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Session

from conftest import (
    insert_telemetry_event,
    seed_cycle_time_scenario,
    seed_discrepancy_scenario,
    seed_fulfillment_scenario,
)


PROCESSING_DATE = date(2026, 6, 30)
DAY_DT = datetime(2026, 6, 30, 0, 0, tzinfo=timezone.utc)


def test_transform_metrics_empty(pipeline_env):
    from telemetry_kpi_daily.stages.transform import transform_metrics

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    assert metrics["order_fulfillment_rate"] == []
    assert metrics["stock_discrepancy_frequency"] == []
    assert metrics["receiving_dispatch_cycle_time"] == []


def test_fulfillment_rate_excludes_non_stock_failures(pipeline_env):
    from telemetry.analysis import compute_fulfillment_rate
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_fulfillment_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        via_stage = transform_metrics(session, PROCESSING_DATE)
        via_analysis = compute_fulfillment_rate(session, PROCESSING_DATE, PROCESSING_DATE)

    assert via_stage["order_fulfillment_rate"] == via_analysis
    point = via_stage["order_fulfillment_rate"][0]
    assert point["warehouse"] == "los_angeles"
    assert point["successful"] == 2
    assert point["failed_insufficient"] == 1
    assert point["fulfillment_rate_pct"] == 66.67


def test_stock_discrepancy_frequency_by_warehouse(pipeline_env):
    from telemetry.analysis import compute_stock_discrepancy_frequency
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_discrepancy_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        via_stage = transform_metrics(session, PROCESSING_DATE)
        via_analysis = compute_stock_discrepancy_frequency(
            session, PROCESSING_DATE, PROCESSING_DATE
        )

    assert via_stage["stock_discrepancy_frequency"] == via_analysis
    point = via_stage["stock_discrepancy_frequency"][0]
    assert point["warehouse"] == "zaragoza"
    assert point["rejection_count"] == 1


def test_receiving_dispatch_cycle_time_fifo(pipeline_env):
    from telemetry.analysis import compute_receiving_dispatch_cycle_time
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_cycle_time_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        via_stage = transform_metrics(session, PROCESSING_DATE)
        via_analysis = compute_receiving_dispatch_cycle_time(
            session, PROCESSING_DATE, PROCESSING_DATE
        )

    assert via_stage["receiving_dispatch_cycle_time"] == via_analysis
    point = via_stage["receiving_dispatch_cycle_time"][0]
    assert point["warehouse"] == "los_angeles"
    assert point["avg_cycle_hours"] == 6.0


def test_warehouse_segmentation_never_mixed(pipeline_env):
    from telemetry_kpi_daily.stages.transform import transform_metrics

    for wh in ("los_angeles", "zaragoza"):
        insert_telemetry_event(
            pipeline_env,
            event_type="dispatch_order_created",
            occurred_at=DAY_DT.replace(hour=10),
            warehouse=wh,
            payload={
                "dispatch_order_id": 1 if wh == "los_angeles" else 2,
                "sku_id": 10,
                "sku_code": "TF-ELEC-0010",
                "client_id": "00000000-0000-0000-0000-000000000001",
                "quantity": 1,
                "destination_country": "US" if wh == "los_angeles" else "ES",
                "carrier": "FedEx",
                "created_by": "00000000-0000-0000-0000-000000000002",
                "created_at": DAY_DT.isoformat().replace("+00:00", "Z"),
                "stock_after_dispatch": 10,
            },
        )

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    warehouses = {row["warehouse"] for row in metrics["order_fulfillment_rate"]}
    assert warehouses == {"los_angeles", "zaragoza"}
    assert len(metrics["order_fulfillment_rate"]) == 2
