from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models import ExitType, SKUCategory, WarehouseCode


class SKUCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    category: SKUCategory
    warehouse: WarehouseCode


class SKURead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    client_name: str
    category: SKUCategory
    warehouse: WarehouseCode
    current_stock: int


class StockEntryCreate(BaseModel):
    sku_id: int
    quantity: int = Field(gt=0)
    reference: str = Field(min_length=1)
    warehouse: WarehouseCode


class StockEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: int
    quantity: int
    reference: str
    warehouse: WarehouseCode
    created_at: datetime
    user_uuid: str


class StockExitCreate(BaseModel):
    sku_id: int
    quantity: int = Field(gt=0)
    exit_type: ExitType
    tracking_number: str | None = None
    warehouse: WarehouseCode

    @model_validator(mode="after")
    def validate_tracking_number(self) -> "StockExitCreate":
        if self.exit_type == ExitType.DISPATCH and not self.tracking_number:
            raise ValueError("tracking_number is required when exit_type is 'dispatch'.")
        if self.exit_type == ExitType.LOSS and self.tracking_number is not None:
            raise ValueError("tracking_number must be null when exit_type is 'loss'.")
        return self


class StockExitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: int
    quantity: int
    exit_type: ExitType
    tracking_number: str | None
    warehouse: WarehouseCode
    created_at: datetime
    user_uuid: str


class InventoryMovementRead(BaseModel):
    id: int
    movement_type: str
    sku_id: int
    sku: str
    sku_name: str
    client_name: str
    category: SKUCategory
    quantity: int
    warehouse: WarehouseCode
    created_at: datetime
    user_uuid: str
    reference: str | None = None
    exit_type: ExitType | None = None
    tracking_number: str | None = None
