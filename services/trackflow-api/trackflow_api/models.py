from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


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
