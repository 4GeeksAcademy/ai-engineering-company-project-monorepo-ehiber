from datetime import datetime, timezone
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
