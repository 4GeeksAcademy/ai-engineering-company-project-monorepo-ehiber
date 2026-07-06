"""Tests for the nightly telemetry script (DEV-53)."""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from sqlmodel import Session

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "nightly_telemetry.py"
TARGET_DATE = date(2026, 6, 30)


def _insert_event(session: Session, *, occurred_at: datetime, event_type: str = "user_login_failed") -> None:
    from trackflow_api.models import TelemetryEvent

    session.add(
        TelemetryEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=occurred_at,
            source="trackflow-api",
            tags={},
            payload={"failure_reason": "invalid_credentials"},
            processing_mode="batch",
        )
    )
    session.commit()


def _run_script(
    monkeypatch,
    tmp_path: Path,
    *,
    target_date: str | None = None,
    raw_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {
        **dict(monkeypatch._env_changes if hasattr(monkeypatch, "_env_changes") else {}),
        "TRACKFLOW_JWT_SECRET_KEY": "test-secret",
        "TRACKFLOW_DATABASE_PATH": str(tmp_path / "app.json"),
        "SUPABASE_URI": f"sqlite:///{tmp_path / 'inventory.db'}",
    }
    if target_date:
        env["TARGET_DATE"] = target_date

    import os

    full_env = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    return tmp_path / "raw"


def test_state_machine_reaches_completed(monkeypatch, tmp_path, raw_dir):
    from trackflow_api.core.database import get_inventory_engine, init_db
    from trackflow_api.models import JobRun
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())
    get_settings = __import__(
        "trackflow_api.core.config", fromlist=["get_settings"]
    ).get_settings
    get_settings.cache_clear()

    init_db()
    engine = get_inventory_engine()
    with Session(engine) as session:
        _insert_event(
            session,
            occurred_at=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
        )

    def _fake_pipeline(processing_date: date):
        assert processing_date == TARGET_DATE
        return {"status": "succeeded", "error": None}

    monkeypatch.setattr(service, "_trigger_pipeline", _fake_pipeline)

    exit_code = service.run_nightly_telemetry(raw_dir=raw_dir)
    assert exit_code == 0

    csv_path = raw_dir / f"telemetry_{TARGET_DATE.isoformat()}.csv"
    assert csv_path.exists()
    assert "user_login_failed" in csv_path.read_text(encoding="utf-8")

    with Session(engine) as session:
        runs = list(session.exec(
            __import__("sqlmodel", fromlist=["select"]).select(JobRun).where(
                JobRun.job_name == NIGHTLY_TELEMETRY_JOB,
                JobRun.target_date == TARGET_DATE,
            )
        ))
        assert len(runs) == 1
        assert runs[0].status == "completed"
        assert runs[0].csv_path == str(csv_path)


def test_failure_marks_job_failed_not_processing(monkeypatch, tmp_path, raw_dir):
    from trackflow_api.core.database import get_inventory_engine, init_db
    from trackflow_api.models import JobRun
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())

    init_db()
    engine = get_inventory_engine()

    def _boom(_target_date: date) -> None:
        raise RuntimeError("pipeline exploded")

    monkeypatch.setattr(service, "_trigger_pipeline", _boom)

    exit_code = service.run_nightly_telemetry(raw_dir=raw_dir)
    assert exit_code == 1

    with Session(engine) as session:
        run = session.exec(
            __import__("sqlmodel", fromlist=["select"]).select(JobRun).where(
                JobRun.job_name == NIGHTLY_TELEMETRY_JOB,
                JobRun.target_date == TARGET_DATE,
            )
        ).first()
        assert run is not None
        assert run.status == "failed"
        assert "pipeline exploded" in (run.error_message or "")


def test_idempotent_second_run_skips_work(monkeypatch, tmp_path, raw_dir):
    from trackflow_api.core.database import get_inventory_engine, init_db
    from trackflow_api.models import JobRun
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())

    init_db()
    engine = get_inventory_engine()
    with Session(engine) as session:
        _insert_event(
            session,
            occurred_at=datetime(2026, 6, 30, 8, 0, tzinfo=timezone.utc),
        )

    calls = {"count": 0}

    def _fake_pipeline(_processing_date: date):
        calls["count"] += 1
        return {"status": "succeeded", "error": None}

    monkeypatch.setattr(service, "_trigger_pipeline", _fake_pipeline)

    assert service.run_nightly_telemetry(raw_dir=raw_dir) == 0
    assert service.run_nightly_telemetry(raw_dir=raw_dir) == 0
    assert calls["count"] == 1

    csv_path = raw_dir / f"telemetry_{TARGET_DATE.isoformat()}.csv"
    assert csv_path.exists()

    with Session(engine) as session:
        runs = list(session.exec(
            __import__("sqlmodel", fromlist=["select"]).select(JobRun).where(
                JobRun.job_name == NIGHTLY_TELEMETRY_JOB,
                JobRun.target_date == TARGET_DATE,
            )
        ))
        assert len(runs) == 1


def test_csv_not_duplicated_when_file_exists(monkeypatch, tmp_path, raw_dir):
    from trackflow_api.core.database import get_inventory_engine, init_db
    from trackflow_api.models import JobRun
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / f"telemetry_{TARGET_DATE.isoformat()}.csv"
    csv_path.write_text("existing-content\n", encoding="utf-8")

    init_db()
    engine = get_inventory_engine()
    with Session(engine) as session:
        _insert_event(
            session,
            occurred_at=datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc),
        )

    monkeypatch.setattr(service, "_trigger_pipeline", lambda _d: None)

    service.run_nightly_telemetry(raw_dir=raw_dir)
    assert csv_path.read_text(encoding="utf-8") == "existing-content\n"


def test_distributed_lock_prevents_parallel_runs(monkeypatch, tmp_path, raw_dir):
    import threading

    from trackflow_api.core.database import get_inventory_engine, init_db
    from trackflow_api.models import JobRun
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())
    init_db()
    engine = get_inventory_engine()

    start_barrier = threading.Barrier(2)
    pipeline_barrier = threading.Event()
    release = threading.Event()

    def _slow_pipeline(_processing_date: date):
        pipeline_barrier.set()
        release.wait(timeout=5)

    monkeypatch.setattr(service, "_trigger_pipeline", _slow_pipeline)

    results: list[int] = []

    def _run() -> None:
        start_barrier.wait(timeout=5)
        results.append(service.run_nightly_telemetry(raw_dir=raw_dir))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run), pool.submit(_run)]
        pipeline_barrier.wait(timeout=5)
        release.set()
        for future in futures:
            future.result(timeout=10)

    assert sorted(results) == [0, 0]
    assert results.count(0) == 2

    with Session(engine) as session:
        runs = list(session.exec(
            __import__("sqlmodel", fromlist=["select"]).select(JobRun).where(
                JobRun.job_name == NIGHTLY_TELEMETRY_JOB,
                JobRun.target_date == TARGET_DATE,
            )
        ))
        assert len(runs) == 1


def test_logs_include_timestamp_job_and_status(monkeypatch, tmp_path, raw_dir, capsys):
    from trackflow_api.core.database import init_db
    from trackflow_api.repositories.job_run_repository import NIGHTLY_TELEMETRY_JOB
    from trackflow_api.services import nightly_telemetry_service as service

    monkeypatch.setenv("TARGET_DATE", TARGET_DATE.isoformat())
    init_db()
    monkeypatch.setattr(service, "_trigger_pipeline", lambda _d: None)

    service.run_nightly_telemetry(raw_dir=raw_dir)
    output = capsys.readouterr().out
    lines = [line for line in output.splitlines() if line.strip()]
    assert lines

    events = [json.loads(line) for line in lines]
    statuses = {event["status"] for event in events}
    assert "pending" in statuses
    assert "processing" in statuses
    assert "completed" in statuses
    for event in events:
        assert event["job"] == NIGHTLY_TELEMETRY_JOB
        assert "timestamp" in event
        assert event["target_date"] == TARGET_DATE.isoformat()


def test_resolve_target_date_from_env(monkeypatch):
    from trackflow_api.services.nightly_telemetry_service import resolve_target_date

    monkeypatch.setenv("TARGET_DATE", "2026-05-15")
    assert resolve_target_date() == date(2026, 5, 15)

    monkeypatch.delenv("TARGET_DATE", raising=False)
    resolved = resolve_target_date()
    assert resolved == datetime.now(timezone.utc).date() - __import__("datetime").timedelta(days=1)
