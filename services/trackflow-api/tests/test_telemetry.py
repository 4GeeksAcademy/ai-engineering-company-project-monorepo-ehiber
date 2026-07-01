"""
Tests de aceptación para el endpoint de telemetría Phase 3.

Verifica que los eventos válidos se persisten, los inválidos se rechazan
individualmente, y la respuesta refleja correctamente stored/rejected.
"""

from uuid import uuid4

from fastapi.testclient import TestClient


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _valid_event(
    event_name: str = "user_login_failed",
    **overrides: object,
) -> dict:
    """Build a minimal valid telemetry event."""
    event = {
        "event_id": str(uuid4()),
        "event_name": event_name,
        "event_version": "1.0",
        "occurred_at": "2026-06-30T12:00:00Z",
        "source": "trackflow-api",
        "warehouse": None,
        "correlation_id": None,
        "processing_mode": "batch",
        "payload": {},
    }
    event.update(overrides)
    return event


# ─── Happy path ─────────────────────────────────────────────────


def test_telemetry_batch_all_valid():
    """Todos los eventos son válidos → stored=N, rejected=0."""
    client = _client()

    events = [
        _valid_event(
            event_name="user_login_failed",
            payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123"},
        ),
        _valid_event(
            event_name="dispatch_form_abandoned",
            warehouse="los_angeles",
            source="backoffice-web",
            payload={"warehouse": "los_angeles", "form_session_id": "sess-1", "seconds_on_form": 45},
        ),
        _valid_event(
            event_name="product_list_viewed",
            warehouse="zaragoza",
            source="backoffice-web",
            payload={"product_count": 12},
        ),
    ]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 3
    assert data["stored"] == 3
    assert data["rejected"] == 0


def test_telemetry_batch_empty():
    """Batch vacío → stored=0, rejected=0."""
    client = _client()

    response = client.post("/telemetry/events", json={"events": []})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 0
    assert data["stored"] == 0
    assert data["rejected"] == 0


# ─── Rejection scenarios ───────────────────────────────────────


def test_telemetry_rejects_extra_payload_keys():
    """Payload con claves no permitidas → rechazado individualmente."""
    client = _client()

    events = [
        _valid_event(
            event_name="user_login_failed",
            payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123"},
        ),
        _valid_event(
            event_name="user_login_failed",
            payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123", "extra_key": "nope"},
        ),
    ]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 2
    assert data["stored"] == 1
    assert data["rejected"] == 1


def test_telemetry_rejects_missing_warehouse():
    """Evento de almacén sin warehouse → rechazado."""
    client = _client()

    events = [
        _valid_event(
            event_name="dispatch_order_created",
            warehouse=None,
            payload={
                "dispatch_order_id": 1,
                "sku_id": 1,
                "sku_code": "TEST-001",
                "client_id": str(uuid4()),
                "warehouse": "los_angeles",
                "quantity": 10,
                "destination_country": "US",
                "carrier": "FedEx",
                "created_by": str(uuid4()),
                "created_at": "2026-06-30T12:00:00Z",
                "stock_after_dispatch": 50,
            },
        ),
    ]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 1
    assert data["stored"] == 0
    assert data["rejected"] == 1


def test_telemetry_rejects_wrong_source():
    """Evento que requiere backoffice-web pero llega con trackflow-api → rechazado."""
    client = _client()

    events = [
        _valid_event(
            event_name="dispatch_form_abandoned",
            warehouse="zaragoza",
            source="trackflow-api",
            payload={"warehouse": "zaragoza", "form_session_id": "sess-1", "seconds_on_form": 30},
        ),
    ]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 1
    assert data["stored"] == 0
    assert data["rejected"] == 1


def test_telemetry_mixed_batch_partial_rejection():
    """Batch mixto: algunos válidos, otros no → los válidos se persisten."""
    client = _client()

    events = [
        _valid_event(
            event_name="user_login_failed",
            payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123"},
        ),
        _valid_event(
            event_name="user_login_failed",
            payload={"failure_reason": "invalid_credentials"},  # falta source_ip_hash (no es required)
        ),
        _valid_event(
            event_name="dispatch_form_abandoned",
            warehouse="los_angeles",
            source="trackflow-api",  # source incorrecto
            payload={"warehouse": "los_angeles", "form_session_id": "sess-1", "seconds_on_form": 45},
        ),
    ]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 3
    assert data["stored"] == 2  # dos user_login_failed son válidos
    assert data["rejected"] == 1


# ─── Persistence verification ──────────────────────────────────


def test_telemetry_events_are_persisted():
    """Los eventos almacenados se pueden leer desde la base de datos."""
    from sqlmodel import Session, select

    from trackflow_api.core.database import get_inventory_engine
    from trackflow_api.models import TelemetryEvent

    client = _client()
    event_id = str(uuid4())

    client.post(
        "/telemetry/events",
        json={
            "events": [
                _valid_event(
                    event_id=event_id,
                    event_name="user_login_failed",
                    payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123"},
                ),
            ]
        },
    )

    engine = get_inventory_engine()
    with Session(engine) as session:
        result = session.exec(
            select(TelemetryEvent).where(TelemetryEvent.event_id == event_id)
        ).first()

    assert result is not None
    assert result.event_type == "user_login_failed"
    assert result.timestamp.isoformat().startswith("2026-06-30T12:00:00")
    assert result.tags["event_version"] == "1.0"
    assert result.tags["warehouse"] is None
    assert result.tags["correlation_id"] is None
    assert result.source == "trackflow-api"
    assert result.payload["failure_reason"] == "invalid_credentials"


def test_telemetry_idempotent_event_id_unique():
    """Mismo event_id repetido → viola unique constraint y se rechaza."""
    client = _client()
    same_id = str(uuid4())

    event = {
        "events": [
            _valid_event(
                event_id=same_id,
                event_name="user_login_failed",
                payload={"failure_reason": "invalid_credentials", "source_ip_hash": "abc123"},
            ),
        ]
    }

    # Primer envío → stored=1
    r1 = client.post("/telemetry/events", json=event)
    assert r1.json()["stored"] == 1

    # Segundo envío con el mismo event_id → falla por unique constraint
    r2 = client.post("/telemetry/events", json=event)
    assert r2.status_code == 200
    data = r2.json()
    assert data["stored"] == 0
    assert data["rejected"] == 1