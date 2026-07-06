from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"
REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "docs" / "telemetry" / "event-schemas.json"


@dataclass(frozen=True)
class PipelineConfig:
    pipeline_name: str
    schema_version: str
    late_data_days: int
    skip_if_success_within_hours: int
    schedule_cron: str
    kpi_event_types: tuple[str, ...]
    extract_retries: int
    extract_retry_delay_seconds: int
    load_retries: int
    load_retry_delay_seconds: int


def load_config(path: Path | None = None) -> PipelineConfig:
    config_path = path or CONFIG_PATH
    raw: dict[str, Any] = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    retry = raw.get("retry", {})
    extract_retry = retry.get("extract", {})
    load_retry = retry.get("load", {})
    return PipelineConfig(
        pipeline_name=raw["pipeline_name"],
        schema_version=str(raw["schema_version"]),
        late_data_days=int(raw["late_data_days"]),
        skip_if_success_within_hours=int(raw["skip_if_success_within_hours"]),
        schedule_cron=str(raw["schedule_cron"]),
        kpi_event_types=tuple(raw["kpi_event_types"]),
        extract_retries=int(extract_retry.get("retries", 3)),
        extract_retry_delay_seconds=int(extract_retry.get("delay_seconds", 30)),
        load_retries=int(load_retry.get("retries", 3)),
        load_retry_delay_seconds=int(load_retry.get("delay_seconds", 30)),
    )


def resolve_processing_dates(
    *,
    processing_date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    late_data_days: int = 3,
) -> list[date]:
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("start_date must be on or before end_date")
        days: list[date] = []
        current = start_date
        while current <= end_date:
            days.append(current)
            current += timedelta(days=1)
        return days

    anchor = processing_date or (datetime.now(timezone.utc).date() - timedelta(days=1))
    start = anchor - timedelta(days=late_data_days - 1)
    days = []
    current = start
    while current <= anchor:
        days.append(current)
        current += timedelta(days=1)
    return days
