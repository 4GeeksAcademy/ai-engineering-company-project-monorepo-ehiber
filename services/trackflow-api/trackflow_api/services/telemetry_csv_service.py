"""CSV export helpers for persisted telemetry events."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, time, timedelta, timezone
from io import StringIO
from pathlib import Path

from sqlmodel import Session, select

from ..core.config import REPO_ROOT
from ..models import TelemetryEvent


def day_bounds(target_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    return start_dt, end_dt


def telemetry_csv_path(target_date: date, *, raw_dir: Path | None = None) -> Path:
    base = raw_dir or (REPO_ROOT / "data" / "raw")
    return base / f"telemetry_{target_date.isoformat()}.csv"


def list_events_for_date(session: Session, target_date: date) -> list[TelemetryEvent]:
    start_dt, end_dt = day_bounds(target_date)
    statement = (
        select(TelemetryEvent)
        .where(TelemetryEvent.timestamp >= start_dt)
        .where(TelemetryEvent.timestamp < end_dt)
        .order_by(TelemetryEvent.timestamp, TelemetryEvent.event_id)
    )
    return list(session.exec(statement).all())


def events_to_csv(events: list[TelemetryEvent]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "event_id",
            "event_type",
            "timestamp",
            "source",
            "processing_mode",
            "tags",
            "payload",
            "created_at",
        ]
    )
    for event in events:
        writer.writerow(
            [
                event.event_id,
                event.event_type,
                event.timestamp.isoformat(),
                event.source,
                event.processing_mode,
                json.dumps(event.tags or {}, sort_keys=True),
                json.dumps(event.payload or {}, sort_keys=True),
                event.created_at.isoformat(),
            ]
        )
    return output.getvalue()


def export_telemetry_csv_if_missing(
    session: Session,
    target_date: date,
    *,
    raw_dir: Path | None = None,
) -> Path:
    destination = telemetry_csv_path(target_date, raw_dir=raw_dir)
    if destination.exists():
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    events = list_events_for_date(session, target_date)
    destination.write_text(events_to_csv(events), encoding="utf-8", newline="")
    return destination
