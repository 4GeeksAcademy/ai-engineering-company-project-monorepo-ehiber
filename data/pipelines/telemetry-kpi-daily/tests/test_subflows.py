"""Tests for subflow phase runners (no Prefect runtime required)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from conftest import seed_fulfillment_scenario


def test_coalesce_validation_continues_on_failure():
    from telemetry_kpi_daily.phases import coalesce_validation

    extracted = {
        "processing_date": "2026-06-30",
        "events": [{"event_id": "1"}],
        "events_extracted": 1,
        "cursor": {},
    }
    failed_state = MagicMock()
    failed_state.is_completed.return_value = False
    failed_state.message = "schema file missing"

    result = coalesce_validation(extracted, failed_state)

    assert result["validation_skipped"] is True
    assert result["events_extracted"] == 1
    assert result["events_rejected"] == 0


def test_run_validate_phase_counts_rejections():
    from telemetry_kpi_daily.phases import run_validate_phase

    extracted = {
        "events": [
            {"event_id": "1", "event_type": "unknown", "warehouse": "los_angeles", "payload": {}}
        ],
        "events_extracted": 1,
    }
    result = run_validate_phase(extracted)
    assert result["events_rejected"] == 1


def test_run_transform_phase_matches_fulfillment(pipeline_env):
    from telemetry_kpi_daily.phases import run_transform_phase

    day = datetime(2026, 6, 30, tzinfo=timezone.utc)
    seed_fulfillment_scenario(pipeline_env, day=day)

    result = run_transform_phase(date(2026, 6, 30))
    assert len(result["metrics"]["order_fulfillment_rate"]) == 1
    assert result["metrics"]["order_fulfillment_rate"][0]["fulfillment_rate_pct"] == 66.67
