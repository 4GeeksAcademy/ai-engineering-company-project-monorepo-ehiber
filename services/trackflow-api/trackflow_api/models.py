from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field, SQLModel


class SKUCategory(str, Enum):
    FASHION = "fashion"
    ELECTRONICS = "electronics"
    COSMETICS = "cosmetics"


class WarehouseCode(str, Enum):
    LA = "LA"
    ZGZ = "ZGZ"


class ExitType(str, Enum):
    DISPATCH = "dispatch"
    LOSS = "loss"


class SKU(SQLModel, table=True):
    __tablename__ = "skus"
    __table_args__ = (UniqueConstraint("sku", "warehouse", name="uq_sku_warehouse"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True)
    client_name: str
    category: SKUCategory
    warehouse: WarehouseCode = Field(index=True)


class StockEntry(SQLModel, table=True):
    __tablename__ = "stock_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="skus.id", index=True)
    quantity: int = Field(gt=0)
    reference: str
    warehouse: WarehouseCode = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    user_uuid: str = Field(index=True)


class StockExit(SQLModel, table=True):
    __tablename__ = "stock_exits"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="skus.id", index=True)
    quantity: int = Field(gt=0)
    exit_type: ExitType
    tracking_number: Optional[str] = None
    warehouse: WarehouseCode = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    user_uuid: str = Field(index=True)


class TelemetryEvent(SQLModel, table=True):
    __tablename__ = "telemetry_events"

    event_id: str = Field(primary_key=True, description="Client-provided UUID v4")
    event_type: str = Field(index=True, description="Canonical entity_action name")
    timestamp: datetime = Field(index=True, description="Business fact timestamp (UTC)")
    source: str = Field(description="trackflow-api | backoffice-web")
    tags: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    processing_mode: str = Field(index=True, description="stream | batch")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server-side ingestion timestamp",
    )


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    run_id: str = Field(primary_key=True, description="UUID for this pipeline execution")
    pipeline_name: str = Field(index=True)
    processing_date: date = Field(index=True)
    status: str = Field(index=True, description="pending|running|succeeded|failed|partial|skipped")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = Field(default=None)
    events_extracted: int = Field(default=0)
    events_rejected: int = Field(default=0)
    metrics_written: int = Field(default=0)
    watermark_before: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    watermark_after: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    error_summary: str | None = Field(default=None)
    triggered_by: str = Field(default="manual")


class PipelineWatermark(SQLModel, table=True):
    __tablename__ = "pipeline_watermarks"

    pipeline_name: str = Field(primary_key=True)
    last_occurred_at: datetime | None = Field(default=None)
    last_event_id: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by_run_id: str | None = Field(default=None)


class TelemetryKpiDaily(SQLModel, table=True):
    __tablename__ = "telemetry_kpi_daily"
    __table_args__ = (
        UniqueConstraint(
            "metric_name",
            "business_date",
            "warehouse",
            "dimensions_key",
            name="uq_telemetry_kpi_daily",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    metric_name: str = Field(index=True)
    business_date: date = Field(index=True)
    warehouse: str = Field(index=True)
    dimensions_key: str = Field(index=True, description="Stable key derived from dimensions JSON")
    dimensions: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    value: float | None = Field(default=None)
    sample_size: int | None = Field(default=None)
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_run_id: str = Field(index=True)
    schema_version: str = Field(default="1.0")
