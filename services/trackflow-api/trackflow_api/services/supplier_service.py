from ..repositories import supplier_repository
from ..schemas.suppliers import (
    COUNTRY_CURRENCY,
    SupplierCreate,
    SupplierPublic,
    SupplierRateUpdate,
    SupplierStatusUpdate,
)


def _to_public(record: dict) -> SupplierPublic:
    return SupplierPublic.model_validate(record)


def list_suppliers(*, country: str | None = None, category: str | None = None) -> list[SupplierPublic]:
    records = supplier_repository.list_supplier_records(country=country, category=category)
    return [_to_public(record) for record in records]


def get_supplier(supplier_id: int) -> SupplierPublic | None:
    record = supplier_repository.get_supplier_by_id(supplier_id)
    return _to_public(record) if record else None


def create_supplier(payload: SupplierCreate) -> SupplierPublic:
    expected_currency = COUNTRY_CURRENCY[payload.country]
    record = supplier_repository.create_supplier_record(
        {
            "name": payload.name,
            "country": payload.country.value,
            "categories": [category.value for category in payload.categories],
            "rate_per_shipment": payload.rate_per_shipment,
            "currency": expected_currency,
            "rate_updated_at": supplier_repository.current_timestamp(),
            "status": payload.status.value,
            "service_zone": payload.service_zone,
            "contact_email": payload.contact_email,
            "notes": payload.notes,
        }
    )
    return _to_public(record)


def update_supplier_rate(supplier_id: int, payload: SupplierRateUpdate) -> SupplierPublic | None:
    record = supplier_repository.update_supplier_record(
        supplier_id,
        {
            "rate_per_shipment": payload.rate_per_shipment,
            "rate_updated_at": supplier_repository.current_timestamp(),
        },
    )
    return _to_public(record) if record else None


def update_supplier_status(
    supplier_id: int,
    payload: SupplierStatusUpdate,
) -> SupplierPublic | None:
    record = supplier_repository.update_supplier_record(
        supplier_id,
        {"status": payload.status.value},
    )
    return _to_public(record) if record else None


def delete_supplier(supplier_id: int) -> bool:
    return supplier_repository.delete_supplier_record(supplier_id)
