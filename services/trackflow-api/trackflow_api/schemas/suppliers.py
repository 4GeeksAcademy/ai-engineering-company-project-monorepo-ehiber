from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class SupplierCountry(str, Enum):
    USA = "USA"
    SPAIN = "Spain"


class SupplierStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class SupplierCategory(str, Enum):
    CARRIER_LAST_MILE = "carrier_last_mile"
    CARRIER_INTERNATIONAL = "carrier_international"
    WAREHOUSE_SUPPLIES = "warehouse_supplies"
    PACKAGING_MATERIALS = "packaging_materials"
    REVERSE_LOGISTICS = "reverse_logistics"
    FLEET_MAINTENANCE = "fleet_maintenance"
    IT_AND_WMS_SOFTWARE = "it_and_wms_software"
    CLEANING_AND_FACILITIES = "cleaning_and_facilities"


COUNTRY_CURRENCY = {
    SupplierCountry.USA: "USD",
    SupplierCountry.SPAIN: "EUR",
}


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    country: SupplierCountry
    categories: list[SupplierCategory] = Field(min_length=1)
    rate_per_shipment: float = Field(gt=0)
    status: SupplierStatus = SupplierStatus.ACTIVE
    service_zone: str | None = None
    contact_email: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_currency_consistency(self) -> "SupplierCreate":
        return self


class SupplierRateUpdate(BaseModel):
    rate_per_shipment: float = Field(gt=0)


class SupplierStatusUpdate(BaseModel):
    status: SupplierStatus


class SupplierPublic(BaseModel):
    id: int
    name: str
    country: SupplierCountry
    categories: list[SupplierCategory]
    rate_per_shipment: float
    currency: str
    rate_updated_at: str
    status: SupplierStatus
    service_zone: str | None = None
    contact_email: str | None = None
    notes: str | None = None

    @field_validator("categories", mode="before")
    @classmethod
    def normalize_categories(cls, value: list) -> list:
        return [SupplierCategory(item) if isinstance(item, str) else item for item in value]
