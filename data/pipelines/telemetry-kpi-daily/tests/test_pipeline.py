"""Tests for telemetry KPI daily pipeline."""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

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
    from trackflow_api import models  # noqa: F401 — register SQLModel metadata

    config_module.get_settings.cache_clear()
    database_module.get_inventory_engine.cache_clear()

    engine = create_engine(uri, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def _insert_dispatch_created(engine, *, occurred_at: datetime, warehouse: str = "los_angeles"):
    from trackflow_api.models import TelemetryEvent

    event_id = str(uuid4())
    with Session(engine) as session:
        session.add(
            TelemetryEvent(
                event_id=event_id,
                event_type="dispatch_order_created",
                timestamp=occurred_at,
                source="trackflow-api",
                tags={"warehouse": warehouse},
                payload={
                    "dispatch_order_id": 1,
                    "sku_id": 10,
                    "sku_code": "TF-ELEC-0010",
                    "client_id": str(uuid4()),
                    "warehouse": warehouse,
                    "quantity": 5,
                    "destination_country": "US",
                    "carrier": "FedEx",
                    "created_by": str(uuid4()),
                    "created_at": occurred_at.isoformat().replace("+00:00", "Z"),
                    "stock_after_dispatch": 20,
                },
                processing_mode="batch",
            )
        )
        session.commit()


def test_resolve_processing_dates_uses_late_data_window():
    from telemetry_kpi_daily.config import load_config, resolve_processing_dates

    config = load_config()
    dates = resolve_processing_dates(processing_date=date(2026, 6, 30), late_data_days=config.late_data_days)
    assert dates == [date(2026, 6, 28), date(2026, 6, 29), date(2026, 6, 30)]


def test_validate_rejects_unknown_event_type():
    from telemetry_kpi_daily.stages.validate import validate_events

    valid, rejected = validate_events(
        [{"event_id": "1", "event_type": "unknown", "warehouse": "los_angeles", "payload": {}}]
    )
    assert valid == []
    assert rejected[0]["reason"] == "unknown_event_type"


def test_pipeline_is_idempotent_for_same_processing_date(pipeline_env):
    from trackflow_api.models import TelemetryKpiDaily
    from telemetry_kpi_daily.pipeline_core import process_processing_date

    processing_date = date(2026, 6, 30)
    occurred_at = datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc)
    _insert_dispatch_created(pipeline_env, occurred_at=occurred_at)

    first = process_processing_date(processing_date, triggered_by="manual", force=True)
    second = process_processing_date(processing_date, triggered_by="manual", force=True)

    assert first.status == "succeeded"
    assert second.status == "succeeded"
    assert first.metrics_written == second.metrics_written

    with Session(pipeline_env) as session:
        rows = session.exec(select(TelemetryKpiDaily)).all()
    assert len(rows) >= 1


def test_skip_if_recent_success(pipeline_env):
    from trackflow_api.models import PipelineRun
    from trackflow_api.repositories.pipeline_repository import has_recent_success

    with Session(pipeline_env) as session:
        session.add(
            PipelineRun(
                run_id=str(uuid4()),
                pipeline_name="telemetry-kpi-daily",
                processing_date=date(2026, 6, 30),
                status="succeeded",
                finished_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
        assert has_recent_success(session, processing_date=date(2026, 6, 30)) is True


def test_transform_cache_key_fn():
    from telemetry_kpi_daily.caching import transform_cache_key_fn

    assert transform_cache_key_fn({}, {"processing_date": date(2026, 6, 30)}) == (
        "transform-kpi-metrics:2026-06-30"
    )


def test_pipeline_module_exports_flow():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[2] / "pipeline.py").read_text(encoding="utf-8")
    for symbol in (
        "telemetry_kpi_daily_flow",
        "extract_task",
        "validate_task",
        "transform_task",
        "load_task",
        "extract_subflow",
        "validate_subflow",
        "transform_subflow",
        "load_subflow",
    ):
        assert symbol in source


def test_partial_failure_continues_other_dates(pipeline_env):
    from telemetry_kpi_daily.pipeline_core import run_pipeline

    occurred_at = datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc)
    _insert_dispatch_created(pipeline_env, occurred_at=occurred_at)

    summary = run_pipeline(
        [date(2026, 6, 29), date(2026, 6, 30)],
        triggered_by="manual",
        force=True,
    )
    assert summary["succeeded"] >= 1
    assert summary["failed"] + summary["succeeded"] + summary["skipped"] == 2


def test_recent_success_skips_second_run(pipeline_env):
    from telemetry_kpi_daily.pipeline_core import process_processing_date

    processing_date = date(2026, 6, 30)
    occurred_at = datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc)
    _insert_dispatch_created(pipeline_env, occurred_at=occurred_at)

    first = process_processing_date(processing_date, triggered_by="manual", force=True)
    second = process_processing_date(processing_date, triggered_by="manual", force=False)

    assert first.status == "succeeded"
    assert second.status == "skipped"
