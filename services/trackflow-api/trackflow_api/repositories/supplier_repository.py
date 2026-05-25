from datetime import datetime, timezone

from tinydb import Query

from ..core.database import get_db


SUPPLIERS_TABLE = "suppliers"


def list_supplier_records(
    *,
    country: str | None = None,
    category: str | None = None,
) -> list[dict]:
    db = get_db()
    try:
        records = [_normalize_supplier(record) for record in db.table(SUPPLIERS_TABLE).all()]
    finally:
        db.close()

    if country:
        records = [record for record in records if record["country"] == country]
    if category:
        records = [
            record for record in records if category in record["categories"]
        ]

    return sorted(records, key=lambda item: item["id"])


def get_supplier_by_id(supplier_id: int) -> dict | None:
    supplier_query = Query()
    db = get_db()
    try:
        record = db.table(SUPPLIERS_TABLE).get(supplier_query.id == supplier_id)
        return _normalize_supplier(record) if record else None
    finally:
        db.close()


def get_supplier_by_name_and_country(name: str, country: str) -> dict | None:
    supplier_query = Query()
    db = get_db()
    try:
        record = db.table(SUPPLIERS_TABLE).get(
            (supplier_query.name == name) & (supplier_query.country == country)
        )
        return _normalize_supplier(record) if record else None
    finally:
        db.close()


def create_supplier_record(payload: dict) -> dict:
    db = get_db()
    try:
        table = db.table(SUPPLIERS_TABLE)
        next_id = _next_supplier_id(table.all())
        record = {"id": next_id, **payload}
        table.insert(record)
        return _normalize_supplier(record)
    finally:
        db.close()


def update_supplier_record(supplier_id: int, updates: dict) -> dict | None:
    supplier_query = Query()
    db = get_db()
    try:
        table = db.table(SUPPLIERS_TABLE)
        updated = table.update(updates, supplier_query.id == supplier_id)
        if not updated:
            return None
        record = table.get(supplier_query.id == supplier_id)
        return _normalize_supplier(record) if record else None
    finally:
        db.close()


def delete_supplier_record(supplier_id: int) -> bool:
    supplier_query = Query()
    db = get_db()
    try:
        removed = db.table(SUPPLIERS_TABLE).remove(supplier_query.id == supplier_id)
        return bool(removed)
    finally:
        db.close()


def _next_supplier_id(records: list[dict]) -> int:
    if not records:
        return 1
    return max(int(record.get("id", 0)) for record in records) + 1


def _normalize_supplier(record: dict) -> dict:
    return {
        "id": int(record["id"]),
        "name": record["name"],
        "country": record["country"],
        "categories": list(record["categories"]),
        "rate_per_shipment": float(record["rate_per_shipment"]),
        "currency": record["currency"],
        "rate_updated_at": record["rate_updated_at"],
        "status": record["status"],
        "service_zone": record.get("service_zone"),
        "contact_email": record.get("contact_email"),
        "notes": record.get("notes"),
    }


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
