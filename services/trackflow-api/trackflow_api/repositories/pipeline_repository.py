"""Persistence helpers for telemetry KPI pipeline runs and mart."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, select

from ..models import PipelineRun, PipelineWatermark, TelemetryKpiDaily

PIPELINE_NAME = "telemetry-kpi-daily"
RECENT_SUCCESS_WINDOW = timedelta(hours=1)


def dimensions_key(dimensions: dict[str, Any]) -> str:
    return json.dumps(dimensions, sort_keys=True, separators=(",", ":"))


def create_run(
    session: Session,
    *,
    processing_date: date,
    triggered_by: str,
    watermark_before: dict[str, Any],
    run_id: str | None = None,
) -> PipelineRun:
    run = PipelineRun(
        run_id=run_id or str(uuid4()),
        pipeline_name=PIPELINE_NAME,
        processing_date=processing_date,
        status="running",
        watermark_before=watermark_before,
        triggered_by=triggered_by,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def finalize_run(
    session: Session,
    run: PipelineRun,
    *,
    status: str,
    events_extracted: int,
    events_rejected: int,
    metrics_written: int,
    watermark_after: dict[str, Any],
    error_summary: str | None = None,
) -> PipelineRun:
    run.status = status
    run.finished_at = datetime.now(timezone.utc)
    run.events_extracted = events_extracted
    run.events_rejected = events_rejected
    run.metrics_written = metrics_written
    run.watermark_after = watermark_after
    run.error_summary = error_summary
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def mark_run_skipped(session: Session, run: PipelineRun, *, reason: str) -> PipelineRun:
    return finalize_run(
        session,
        run,
        status="skipped",
        events_extracted=0,
        events_rejected=0,
        metrics_written=0,
        watermark_after=run.watermark_before,
        error_summary=reason,
    )


def has_recent_success(
    session: Session,
    *,
    processing_date: date,
    pipeline_name: str = PIPELINE_NAME,
    within: timedelta = RECENT_SUCCESS_WINDOW,
) -> bool:
    cutoff = datetime.now(timezone.utc) - within
    statement = (
        select(PipelineRun)
        .where(PipelineRun.pipeline_name == pipeline_name)
        .where(PipelineRun.processing_date == processing_date)
        .where(PipelineRun.status == "succeeded")
        .where(PipelineRun.finished_at.is_not(None))
        .where(PipelineRun.finished_at >= cutoff)
    )
    return session.exec(statement).first() is not None


def has_pipeline_success_for_date(
    session: Session,
    *,
    processing_date: date,
    pipeline_name: str = PIPELINE_NAME,
) -> bool:
    statement = (
        select(PipelineRun)
        .where(PipelineRun.pipeline_name == pipeline_name)
        .where(PipelineRun.processing_date == processing_date)
        .where(PipelineRun.status == "succeeded")
    )
    return session.exec(statement).first() is not None


def get_watermark(session: Session, pipeline_name: str = PIPELINE_NAME) -> dict[str, Any]:
    row = session.get(PipelineWatermark, pipeline_name)
    if row is None:
        return {"last_occurred_at": None, "last_event_id": None}
    return {
        "last_occurred_at": row.last_occurred_at.isoformat() if row.last_occurred_at else None,
        "last_event_id": row.last_event_id,
    }


def update_watermark(
    session: Session,
    *,
    pipeline_name: str,
    run_id: str,
    last_occurred_at: datetime | None,
    last_event_id: str | None,
) -> None:
    row = session.get(PipelineWatermark, pipeline_name)
    if row is None:
        row = PipelineWatermark(pipeline_name=pipeline_name)
    row.last_occurred_at = last_occurred_at
    row.last_event_id = last_event_id
    row.updated_at = datetime.now(timezone.utc)
    row.updated_by_run_id = run_id
    session.add(row)
    session.commit()


def upsert_kpi_rows(session: Session, rows: list[TelemetryKpiDaily]) -> int:
    if not rows:
        return 0

    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        payload = [
            {
                "metric_name": row.metric_name,
                "business_date": row.business_date,
                "warehouse": row.warehouse,
                "dimensions_key": row.dimensions_key,
                "dimensions": row.dimensions,
                "value": row.value,
                "sample_size": row.sample_size,
                "computed_at": row.computed_at,
                "pipeline_run_id": row.pipeline_run_id,
                "schema_version": row.schema_version,
            }
            for row in rows
        ]
        statement = pg_insert(TelemetryKpiDaily).values(payload)
        statement = statement.on_conflict_do_update(
            constraint="uq_telemetry_kpi_daily",
            set_={
                "dimensions": statement.excluded.dimensions,
                "value": statement.excluded.value,
                "sample_size": statement.excluded.sample_size,
                "computed_at": statement.excluded.computed_at,
                "pipeline_run_id": statement.excluded.pipeline_run_id,
                "schema_version": statement.excluded.schema_version,
            },
        )
        session.execute(statement)
        session.commit()
        return len(rows)

    written = 0
    for row in rows:
        existing = session.exec(
            select(TelemetryKpiDaily).where(
                TelemetryKpiDaily.metric_name == row.metric_name,
                TelemetryKpiDaily.business_date == row.business_date,
                TelemetryKpiDaily.warehouse == row.warehouse,
                TelemetryKpiDaily.dimensions_key == row.dimensions_key,
            )
        ).first()
        if existing:
            existing.dimensions = row.dimensions
            existing.value = row.value
            existing.sample_size = row.sample_size
            existing.computed_at = row.computed_at
            existing.pipeline_run_id = row.pipeline_run_id
            existing.schema_version = row.schema_version
            session.add(existing)
        else:
            session.add(row)
        written += 1
    session.commit()
    return written


def list_kpi_rows(
    session: Session,
    *,
    start_date: date,
    end_date: date,
) -> list[TelemetryKpiDaily]:
    statement = (
        select(TelemetryKpiDaily)
        .where(TelemetryKpiDaily.business_date >= start_date)
        .where(TelemetryKpiDaily.business_date <= end_date)
        .order_by(TelemetryKpiDaily.business_date, TelemetryKpiDaily.warehouse)
    )
    return list(session.exec(statement).all())


def get_latest_run(
    session: Session,
    *,
    pipeline_name: str = PIPELINE_NAME,
) -> PipelineRun | None:
    statement = (
        select(PipelineRun)
        .where(PipelineRun.pipeline_name == pipeline_name)
        .order_by(PipelineRun.started_at.desc())
    )
    return session.exec(statement).first()


def run_to_metadata(run: PipelineRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "pipeline_name": run.pipeline_name,
        "processing_date": run.processing_date.isoformat(),
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "records_processed": run.events_extracted,
        "metrics_written": run.metrics_written,
        "events_rejected": run.events_rejected,
        "error_summary": run.error_summary,
        "triggered_by": run.triggered_by,
    }
