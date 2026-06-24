from ..core.cache import (
    SUPPLIERS_LIST_PREFIX,
    cache_get,
    cache_invalidate_prefix,
    cache_set,
    suppliers_list_cache_key,
)
from ..repositories import supplier_repository
from ..schemas.suppliers import (
    COUNTRY_CURRENCY,
    SupplierCreate,
    SupplierPublic,
    SupplierRateUpdate,
    SupplierStatusUpdate,
)

SUPPLIERS_CACHE_TTL_SECONDS = 60


def _to_public(record: dict) -> SupplierPublic:
    return SupplierPublic.model_validate(record)


def _invalidate_suppliers_cache() -> None:
    cache_invalidate_prefix(SUPPLIERS_LIST_PREFIX)


def list_suppliers(*, country: str | None = None, category: str | None = None) -> list[SupplierPublic]:
    cache_key = suppliers_list_cache_key(country=country, category=category)
    cached = cache_get(cache_key)
    if cached is not None:
        return [SupplierPublic.model_validate(item) for item in cached]

    records = supplier_repository.list_supplier_records(country=country, category=category)
    suppliers = [_to_public(record) for record in records]
    cache_set(
        cache_key,
        [supplier.model_dump(mode="json") for supplier in suppliers],
        SUPPLIERS_CACHE_TTL_SECONDS,
    )
    return suppliers


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
    _invalidate_suppliers_cache()
    return _to_public(record)


def update_supplier_rate(supplier_id: int, payload: SupplierRateUpdate) -> SupplierPublic | None:
    record = supplier_repository.update_supplier_record(
        supplier_id,
        {
            "rate_per_shipment": payload.rate_per_shipment,
            "rate_updated_at": supplier_repository.current_timestamp(),
        },
    )
    if record:
        _invalidate_suppliers_cache()
    return _to_public(record) if record else None


def update_supplier_status(
    supplier_id: int,
    payload: SupplierStatusUpdate,
) -> SupplierPublic | None:
    record = supplier_repository.update_supplier_record(
        supplier_id,
        {"status": payload.status.value},
    )
    if record:
        _invalidate_suppliers_cache()
    return _to_public(record) if record else None


def delete_supplier(supplier_id: int) -> bool:
    deleted = supplier_repository.delete_supplier_record(supplier_id)
    if deleted:
        _invalidate_suppliers_cache()
    return deleted
