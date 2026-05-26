from datetime import datetime, timezone

from tinydb import Query

from ..core.database import get_db


INCIDENTS_TABLE = "managed_incidents"


def list_incident_records(
    *,
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[dict]:
    db = get_db()
    try:
        records = [_normalize_incident(record) for record in db.table(INCIDENTS_TABLE).all()]
    finally:
        db.close()

    if status:
        records = [record for record in records if record["status"] == status]
    if origin:
        records = [record for record in records if record["origin"] == origin]
    if branch:
        records = [record for record in records if record["branch"] == branch]
    if category:
        records = [record for record in records if record["category"] == category]

    return sorted(records, key=lambda item: item["id"], reverse=True)


def get_incident_by_id(incident_id: int) -> dict | None:
    incident_query = Query()
    db = get_db()
    try:
        record = db.table(INCIDENTS_TABLE).get(incident_query.id == incident_id)
        return _normalize_incident(record) if record else None
    finally:
        db.close()


def get_incident_by_source_id(source_incident_id: str) -> dict | None:
    incident_query = Query()
    db = get_db()
    try:
        record = db.table(INCIDENTS_TABLE).get(
            incident_query.source_incident_id == source_incident_id
        )
        return _normalize_incident(record) if record else None
    finally:
        db.close()


def create_incident_record(payload: dict) -> dict:
    db = get_db()
    try:
        table = db.table(INCIDENTS_TABLE)
        next_id = _next_incident_id(table.all())
        now = current_timestamp()
        record = {
            "id": next_id,
            "created_at": payload.get("created_at", now),
            "updated_at": payload.get("updated_at", now),
            **payload,
        }
        table.insert(record)
        return _normalize_incident(record)
    finally:
        db.close()


def update_incident_record(incident_id: int, updates: dict) -> dict | None:
    incident_query = Query()
    db = get_db()
    try:
        table = db.table(INCIDENTS_TABLE)
        updates = {**updates, "updated_at": current_timestamp()}
        updated = table.update(updates, incident_query.id == incident_id)
        if not updated:
            return None
        record = table.get(incident_query.id == incident_id)
        return _normalize_incident(record) if record else None
    finally:
        db.close()


def summarize_incidents() -> list[dict]:
    db = get_db()
    try:
        return [_normalize_incident(record) for record in db.table(INCIDENTS_TABLE).all()]
    finally:
        db.close()


def _next_incident_id(records: list[dict]) -> int:
    if not records:
        return 1
    return max(int(record.get("id", 0)) for record in records) + 1


def _normalize_incident(record: dict) -> dict:
    return {
        "id": int(record["id"]),
        "title": record["title"],
        "description": record["description"],
        "category": record["category"],
        "status": record["status"],
        "origin": record["origin"],
        "branch": record["branch"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "source_incident_id": record.get("source_incident_id"),
    }


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
