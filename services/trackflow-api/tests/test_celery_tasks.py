"""Tests for Celery task queue endpoints and dead letter handling."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from trackflow_api.core.database import get_inventory_engine
from trackflow_api.models import DeadLetterTask
from trackflow_api.repositories.dead_letter_repository import record_dead_letter_task
from trackflow_api.tasks.pipeline import record_pipeline_task_dlq


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"tasks-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_task_status_requires_auth():
    client = _client()
    response = client.get("/tasks/some-task-id")
    assert response.status_code == 401


def test_pipeline_trigger_returns_202_and_task_id(monkeypatch):
    client = _client()
    headers = _auth_headers(client)

    def fake_delay(payload):
        class _Result:
            id = "task-123"

        return _Result()

    monkeypatch.setattr(
        "trackflow_api.services.task_queue_service.run_telemetry_pipeline_task.delay",
        fake_delay,
    )

    response = client.post(
        "/telemetry/pipeline/run",
        headers=headers,
        json={"processing_date": "2026-06-30", "force": True},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["task_id"] == "task-123"
    assert body["status"] == "pending"


def test_get_task_status_success_after_pipeline_enqueue(monkeypatch):
    client = _client()
    headers = _auth_headers(client)

    monkeypatch.setattr(
        "trackflow_api.tasks.pipeline.run_telemetry_pipeline_direct_job",
        lambda **kwargs: {
            "pipeline_name": "telemetry-kpi-daily",
            "succeeded": 1,
            "skipped": 0,
            "failed": 0,
            "results": [{"status": "succeeded"}],
        },
    )

    trigger = client.post(
        "/telemetry/pipeline/run",
        headers=headers,
        json={"processing_date": "2026-06-30", "force": True},
    )
    assert trigger.status_code == 202
    task_id = trigger.json()["task_id"]

    status_response = client.get(f"/tasks/{task_id}", headers=headers)
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["task_id"] == task_id
    assert payload["status"] == "success"
    assert payload["result"]["succeeded"] == 1


def test_record_pipeline_task_dlq_persists_third_attempt():
    task_id = f"dlq-{uuid4()}"
    payload = {"processing_date": "2026-06-30", "force": True}

    record_pipeline_task_dlq(
        task_id=task_id,
        task_name="trackflow_api.tasks.pipeline.run_telemetry_pipeline_task",
        attempt_number=3,
        error_message="pipeline exploded",
        payload=payload,
    )

    engine = get_inventory_engine()
    with Session(engine) as session:
        row = session.exec(
            select(DeadLetterTask).where(DeadLetterTask.task_id == task_id)
        ).first()
        assert row is not None
        assert row.attempt_number == 3
        assert row.error_message == "pipeline exploded"
        assert row.payload == payload


def test_get_task_status_dead_letter():
    client = _client()
    headers = _auth_headers(client)
    task_id = f"dlq-{uuid4()}"

    engine = get_inventory_engine()
    with Session(engine) as session:
        record_dead_letter_task(
            session,
            task_id=task_id,
            task_name="trackflow_api.tasks.pipeline.run_telemetry_pipeline_task",
            attempt_number=3,
            error_message="final failure",
            payload={"processing_date": "2026-06-30"},
        )

    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dead_letter"
    assert body["attempt_number"] == 3
    assert body["error"] == "final failure"
