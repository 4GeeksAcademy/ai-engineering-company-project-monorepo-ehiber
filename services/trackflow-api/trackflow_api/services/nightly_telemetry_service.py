"""Nightly telemetry orchestration: CSV export, pipeline trigger, job ledger."""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlmodel import Session

from ..core.config import REPO_ROOT
from ..core.database import get_inventory_engine, init_inventory_db
from ..services.telemetry_csv_service import export_telemetry_csv_if_missing
from ..repositories.job_run_repository import (
    NIGHTLY_TELEMETRY_JOB,
    create_job_run,
    get_job_run,
    has_completed_run,
    mark_job_completed,
    mark_job_failed,
    mark_job_processing,
    release_lock,
    try_acquire_lock,
)
from ..repositories.pipeline_repository import has_pipeline_success_for_date
from .pipeline_trigger_service import trigger_telemetry_kpi_daily_direct


def resolve_target_date() -> date:
    raw = os.getenv("TARGET_DATE", "").strip()
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(timezone.utc).date() - timedelta(days=1)


def log_job_event(
    status: str,
    *,
    target_date: date,
    run_id: str | None = None,
    error: str | None = None,
    detail: str | None = None,
) -> None:
    payload: dict[str, str] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "job": NIGHTLY_TELEMETRY_JOB,
        "status": status,
        "target_date": target_date.isoformat(),
    }
    if run_id:
        payload["run_id"] = run_id
    if error:
        payload["error"] = error
    if detail:
        payload["detail"] = detail
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _trigger_pipeline(target_date: date) -> None:
    summary = trigger_telemetry_kpi_daily_direct(
        target_date,
        triggered_by="nightly-script",
        force=False,
    )
    if summary["status"] not in {"succeeded", "skipped"}:
        message = summary.get("error") or f"pipeline finished with status={summary['status']}"
        raise RuntimeError(message)


def run_nightly_telemetry(*, raw_dir: Path | None = None) -> int:
    target_date = resolve_target_date()
    init_inventory_db()
    engine = get_inventory_engine()
    run_id = str(uuid4())
    run = None

    with Session(engine) as session:
        if has_completed_run(session, job_name=NIGHTLY_TELEMETRY_JOB, target_date=target_date):
            log_job_event(
                "completed",
                target_date=target_date,
                detail="already_completed_for_date",
            )
            return 0

        if not try_acquire_lock(session, NIGHTLY_TELEMETRY_JOB, run_id):
            return 0

        try:
            run = create_job_run(
                session,
                run_id=run_id,
                job_name=NIGHTLY_TELEMETRY_JOB,
                target_date=target_date,
                status="pending",
            )
            log_job_event("pending", target_date=target_date, run_id=run_id)

            run = mark_job_processing(session, run)
            log_job_event("processing", target_date=target_date, run_id=run_id)

            csv_path = export_telemetry_csv_if_missing(
                session,
                target_date,
                raw_dir=raw_dir or (REPO_ROOT / "data" / "raw"),
            )

            if not has_pipeline_success_for_date(session, processing_date=target_date):
                _trigger_pipeline(target_date)
            else:
                log_job_event(
                    "processing",
                    target_date=target_date,
                    run_id=run_id,
                    detail="pipeline_already_succeeded",
                )

            run = mark_job_completed(session, run, csv_path=str(csv_path))
            log_job_event("completed", target_date=target_date, run_id=run_id)
            return 0
        except Exception as exc:
            if run is not None:
                mark_job_failed(session, run, str(exc))
            log_job_event(
                "failed",
                target_date=target_date,
                run_id=run_id,
                error=str(exc),
            )
            return 1
        finally:
            release_lock(session, NIGHTLY_TELEMETRY_JOB)
            if run is not None:
                refreshed = get_job_run(session, run.run_id)
                if refreshed is not None and refreshed.status == "processing":
                    mark_job_failed(session, refreshed, "unexpected exit while processing")


def _configure_import_paths() -> None:
    repo_root = REPO_ROOT
    paths = (
        repo_root / "services" / "trackflow-api",
        repo_root / "services",
        repo_root / "data" / "pipelines" / "telemetry-kpi-daily",
        repo_root / "data" / "pipelines",
    )
    for path in paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def main() -> int:
    _configure_import_paths()
    return run_nightly_telemetry()
