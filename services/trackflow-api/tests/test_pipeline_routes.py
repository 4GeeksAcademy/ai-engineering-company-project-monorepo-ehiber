"""Tests for telemetry pipeline API endpoints."""

from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"pipeline-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_latest_pipeline_run_requires_auth():
    client = _client()
    response = client.get("/telemetry/pipeline/runs/latest")
    assert response.status_code == 401


def test_latest_pipeline_run_returns_metadata():
    from trackflow_api.core.database import get_inventory_engine
    from trackflow_api.models import PipelineRun

    client = _client()
    headers = _auth_headers(client)

    run_id = str(uuid4())
    engine = get_inventory_engine()
    with Session(engine) as session:
        session.add(
            PipelineRun(
                run_id=run_id,
                pipeline_name="telemetry-kpi-daily",
                processing_date=date(2026, 6, 30),
                status="succeeded",
                started_at=datetime(2026, 6, 30, 2, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 6, 30, 2, 5, tzinfo=timezone.utc),
                events_extracted=42,
                events_rejected=1,
                metrics_written=6,
                triggered_by="scheduler",
            )
        )
        session.commit()

    response = client.get("/telemetry/pipeline/runs/latest", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == run_id
    assert data["status"] == "succeeded"
    assert data["records_processed"] == 42
    assert data["metrics_written"] == 6
    assert data["started_at"] is not None
    assert data["finished_at"] is not None


def test_trigger_pipeline_run_requires_auth():
    client = _client()
    response = client.post("/telemetry/pipeline/run", json={})
    assert response.status_code == 401


def test_trigger_pipeline_run_enqueues_task(monkeypatch):
    client = _client()
    headers = _auth_headers(client)

    captured: dict = {}

    def fake_enqueue(**kwargs):
        captured.update(kwargs)
        from trackflow_api.schemas.tasks import TaskAcceptedResponse

        return TaskAcceptedResponse(task_id="queued-task-id")

    monkeypatch.setattr(
        "trackflow_api.routes.pipeline.enqueue_telemetry_pipeline_run",
        fake_enqueue,
    )

    response = client.post(
        "/telemetry/pipeline/run",
        headers=headers,
        json={"processing_date": "2026-06-30", "force": True},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["task_id"] == "queued-task-id"
    assert body["status"] == "pending"
    assert captured["processing_date"].isoformat() == "2026-06-30"
    assert captured["force"] is True
