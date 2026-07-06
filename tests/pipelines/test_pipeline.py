"""
Rubric test suite: tests/pipelines/test_pipeline.py

Transformation task unit tests (no Prefect Cloud required).
Domain vocabulary aligned with data/pipelines/PIPELINE_DESIGN.md.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Session

from tests.pipelines.helpers import (
    seed_cycle_time_scenario,
    seed_discrepancy_scenario,
    seed_fulfillment_scenario,
)

PROCESSING_DATE = date(2026, 6, 30)
DAY_DT = datetime(2026, 6, 30, 0, 0, tzinfo=timezone.utc)


def test_transform_kpi_metrics_empty_telemetry_events(pipeline_env):
    """Transform subflow stage: empty raw layer returns empty KPI lists."""
    from telemetry_kpi_daily.stages.transform import transform_metrics

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    assert metrics["order_fulfillment_rate"] == []
    assert metrics["stock_discrepancy_frequency"] == []
    assert metrics["receiving_dispatch_cycle_time"] == []


def test_transform_kpi_metrics_order_fulfillment_rate(pipeline_env):
    """KPI 1 — tasa de cumplimiento por warehouse (los_angeles)."""
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_fulfillment_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    point = metrics["order_fulfillment_rate"][0]
    assert point["warehouse"] == "los_angeles"
    assert point["successful"] == 2
    assert point["failed_insufficient"] == 1
    assert point["fulfillment_rate_pct"] == 66.67


def test_transform_kpi_metrics_stock_discrepancy_frequency(pipeline_env):
    """KPI 2 — frecuencia de direct_stock_edit_rejected por almacén."""
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_discrepancy_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    point = metrics["stock_discrepancy_frequency"][0]
    assert point["warehouse"] == "zaragoza"
    assert point["rejection_count"] == 1


def test_transform_kpi_metrics_receiving_dispatch_cycle_time(pipeline_env):
    """KPI 3 — ciclo recepción-despacho FIFO."""
    from telemetry_kpi_daily.stages.transform import transform_metrics

    seed_cycle_time_scenario(pipeline_env, day=DAY_DT)

    with Session(pipeline_env) as session:
        metrics = transform_metrics(session, PROCESSING_DATE)

    point = metrics["receiving_dispatch_cycle_time"][0]
    assert point["warehouse"] == "los_angeles"
    assert point["avg_cycle_hours"] == 6.0


def test_validate_telemetry_events_rejects_invalid_event_type():
    """Defensive: unknown event_type is rejected by validate stage."""
    from telemetry_kpi_daily.stages.validate import validate_events

    valid, rejected = validate_events(
        [{"event_id": "1", "event_type": "unknown", "warehouse": "los_angeles", "payload": {}}]
    )
    assert valid == []
    assert rejected[0]["reason"] == "unknown_event_type"


def test_main_flow_invokes_etl_subflows():
    """Main flow module documents direct subflow invocations."""
    from pathlib import Path

    flows_source = (
        Path(__file__).resolve().parents[2]
        / "data/pipelines/telemetry-kpi-daily/telemetry_kpi_daily/flows.py"
    ).read_text(encoding="utf-8")
    for name in (
        "extract_subflow",
        "validate_subflow",
        "transform_subflow",
        "load_subflow",
    ):
        assert name in flows_source
    assert "def telemetry_kpi_daily_flow" in flows_source
