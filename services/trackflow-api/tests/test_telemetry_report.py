"""Tests for telemetry KPI report pipeline and GET /telemetry/report."""

from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from trackflow_api.core.cache import cache_set
from trackflow_api.services.telemetry_report_service import _report_cache_key


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"telemetry-report-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _report_query(start: str = "2026-06-24", end: str = "2026-07-01") -> str:
    return f"/telemetry/report?start_date={start}&end_date={end}"


def _dispatch_created_event(
    *,
    occurred_at: str = "2026-06-30T10:00:00Z",
    warehouse: str = "los_angeles",
    dispatch_order_id: int = 1,
    sku_id: int = 10,
    quantity: int = 5,
) -> dict:
    client_id = str(uuid4())
    created_by = str(uuid4())
    return {
        "event_id": str(uuid4()),
        "event_name": "dispatch_order_created",
        "event_version": "1.0",
        "occurred_at": occurred_at,
        "source": "trackflow-api",
        "warehouse": warehouse,
        "correlation_id": None,
        "processing_mode": "batch",
        "payload": {
            "dispatch_order_id": dispatch_order_id,
            "sku_id": sku_id,
            "sku_code": "TF-ELEC-0010",
            "client_id": client_id,
            "warehouse": warehouse,
            "quantity": quantity,
            "destination_country": "US",
            "carrier": "FedEx",
            "created_by": created_by,
            "created_at": occurred_at,
            "stock_after_dispatch": 20,
        },
    }


def _dispatch_failed_event(
    *,
    occurred_at: str = "2026-06-30T11:00:00Z",
    warehouse: str = "los_angeles",
    failure_reason: str = "insufficient_stock",
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_name": "dispatch_order_failed",
        "event_version": "1.0",
        "occurred_at": occurred_at,
        "source": "trackflow-api",
        "warehouse": warehouse,
        "correlation_id": None,
        "processing_mode": "stream",
        "payload": {
            "sku_id": 10,
            "sku_code": "TF-ELEC-0010",
            "client_id": str(uuid4()),
            "warehouse": warehouse,
            "requested_quantity": 50,
            "available_stock": 12,
            "destination_country": "US",
            "failure_reason": failure_reason,
            "is_peak_hours": False,
            "requested_by": str(uuid4()),
        },
    }


def _stock_edit_rejected_event(
    *,
    occurred_at: str = "2026-06-30T09:00:00Z",
    warehouse: str = "zaragoza",
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_name": "direct_stock_edit_rejected",
        "event_version": "1.0",
        "occurred_at": occurred_at,
        "source": "trackflow-api",
        "warehouse": warehouse,
        "correlation_id": None,
        "processing_mode": "stream",
        "payload": {
            "sku_id": 3,
            "sku_code": "TF-FASH-0003",
            "client_id": str(uuid4()),
            "warehouse": warehouse,
            "attempted_stock_value": 999,
            "current_stock": 40,
            "requested_by": str(uuid4()),
            "http_status": 409,
            "rejection_reason": "direct_stock_edit_forbidden",
        },
    }


def _receiving_created_event(
    *,
    occurred_at: str = "2026-06-30T08:00:00Z",
    warehouse: str = "los_angeles",
    receiving_order_id: int = 100,
    sku_id: int = 10,
    quantity: int = 20,
) -> dict:
    client_id = str(uuid4())
    created_by = str(uuid4())
    return {
        "event_id": str(uuid4()),
        "event_name": "receiving_order_created",
        "event_version": "1.0",
        "occurred_at": occurred_at,
        "source": "trackflow-api",
        "warehouse": warehouse,
        "correlation_id": None,
        "processing_mode": "batch",
        "payload": {
            "receiving_order_id": receiving_order_id,
            "sku_id": sku_id,
            "sku_code": "TF-ELEC-0010",
            "client_id": client_id,
            "warehouse": warehouse,
            "quantity": quantity,
            "carrier": "DHL",
            "created_by": created_by,
            "created_at": occurred_at,
        },
    }


def _seed_events(client: TestClient, events: list[dict]) -> None:
    response = client.post("/telemetry/events", json={"events": events})
    assert response.status_code == 200
    assert response.json()["stored"] == len(events)


def test_telemetry_report_requires_authentication():
    client = _client()

    response = client.get(_report_query())

    assert response.status_code == 401


def test_fulfillment_rate_excludes_non_stock_failures():
    client = _client()
    headers = _auth_headers(client)

    _seed_events(
        client,
        [
            _dispatch_created_event(occurred_at="2026-06-30T10:00:00Z"),
            _dispatch_created_event(
                occurred_at="2026-06-30T10:30:00Z",
                dispatch_order_id=2,
            ),
            _dispatch_failed_event(
                occurred_at="2026-06-30T11:00:00Z",
                failure_reason="insufficient_stock",
            ),
            _dispatch_failed_event(
                occurred_at="2026-06-30T11:30:00Z",
                failure_reason="sku_not_found",
            ),
        ],
    )

    response = client.get(_report_query(start="2026-06-30", end="2026-06-30"), headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "period" in data
    assert "metrics" in data
    series = data["metrics"]["order_fulfillment_rate"]
    assert len(series) == 1
    point = series[0]
    assert point["warehouse"] == "los_angeles"
    assert point["date"] == "2026-06-30"
    assert point["successful"] == 2
    assert point["failed_insufficient"] == 1
    assert point["fulfillment_rate_pct"] == 66.67


def test_stock_discrepancy_frequency_by_day_and_warehouse():
    client = _client()
    headers = _auth_headers(client)

    _seed_events(
        client,
        [
            _stock_edit_rejected_event(occurred_at="2026-06-30T09:00:00Z"),
            _stock_edit_rejected_event(occurred_at="2026-06-30T09:30:00Z"),
            _stock_edit_rejected_event(
                occurred_at="2026-07-01T09:00:00Z",
                warehouse="zaragoza",
            ),
        ],
    )

    response = client.get(_report_query(start="2026-06-30", end="2026-07-01"), headers=headers)
    series = response.json()["metrics"]["stock_discrepancy_frequency"]

    assert len(series) == 2
    day_one = next(item for item in series if item["date"] == "2026-06-30")
    day_two = next(item for item in series if item["date"] == "2026-07-01")
    assert day_one["warehouse"] == "zaragoza"
    assert day_one["rejection_count"] == 2
    assert day_two["rejection_count"] == 1


def test_receiving_dispatch_cycle_time_matching():
    client = _client()
    headers = _auth_headers(client)

    _seed_events(
        client,
        [
            _receiving_created_event(
                occurred_at="2026-06-30T08:00:00Z",
                quantity=20,
            ),
            _dispatch_created_event(
                occurred_at="2026-06-30T10:00:00Z",
                quantity=5,
            ),
        ],
    )

    response = client.get(_report_query(start="2026-06-30", end="2026-06-30"), headers=headers)
    series = response.json()["metrics"]["receiving_dispatch_cycle_time"]

    assert len(series) == 1
    point = series[0]
    assert point["warehouse"] == "los_angeles"
    assert point["date"] == "2026-06-30"
    assert point["avg_cycle_hours"] == 2.0
    assert point["sample_size"] == 5


def test_telemetry_report_defaults_to_seven_day_window():
    client = _client()
    headers = _auth_headers(client)

    response = client.get("/telemetry/report", headers=headers)
    assert response.status_code == 200

    period = response.json()["period"]
    start = date.fromisoformat(period["start_date"])
    end = date.fromisoformat(period["end_date"])
    assert (end - start).days == 7


def test_telemetry_report_uses_cache_until_invalidated():
    client = _client()
    headers = _auth_headers(client)
    cache_key = _report_cache_key(date(2026, 6, 30), date(2026, 6, 30))

    cache_set(
        cache_key,
        {
            "period": {
                "start_date": "2026-06-30",
                "end_date": "2026-06-30",
            },
            "metrics": {
                "order_fulfillment_rate": [],
                "stock_discrepancy_frequency": [],
                "receiving_dispatch_cycle_time": [],
            },
        },
        ttl_seconds=60,
    )
    cached_response = client.get(
        _report_query(start="2026-06-30", end="2026-06-30"),
        headers=headers,
    )
    assert cached_response.status_code == 200
    assert cached_response.json()["metrics"]["order_fulfillment_rate"] == []

    _seed_events(client, [_dispatch_created_event()])
    fresh_response = client.get(
        _report_query(start="2026-06-30", end="2026-06-30"),
        headers=headers,
    )
    assert fresh_response.status_code == 200
    assert len(fresh_response.json()["metrics"]["order_fulfillment_rate"]) == 1


def test_analysis_converts_timestamps_before_grouping():
    import sys
    from pathlib import Path

    from sqlmodel import Session

    services_root = Path(__file__).resolve().parents[2]
    if str(services_root) not in sys.path:
        sys.path.insert(0, str(services_root))

    from telemetry.analysis import compute_stock_discrepancy_frequency
    from trackflow_api.core.database import get_inventory_engine
    from trackflow_api.models import TelemetryEvent

    engine = get_inventory_engine()
    with Session(engine) as session:
        session.add(
            TelemetryEvent(
                event_id=str(uuid4()),
                event_type="direct_stock_edit_rejected",
                timestamp=__import__("datetime").datetime(
                    2026, 6, 30, 12, 0, tzinfo=__import__("datetime").timezone.utc
                ),
                source="trackflow-api",
                tags={"warehouse": "los_angeles"},
                payload={"warehouse": "los_angeles"},
                processing_mode="stream",
            )
        )
        session.commit()

        series = compute_stock_discrepancy_frequency(
            session,
            date(2026, 6, 30),
            date(2026, 6, 30),
        )

    assert len(series) == 1
    assert series[0]["date"] == "2026-06-30"
    assert series[0]["warehouse"] == "los_angeles"
