from datetime import datetime, timezone
from uuid import uuid4

from tinydb import Query

from ..core.database import get_db


USERS_TABLE = "users"


def create_user_record(
    *,
    email: str,
    hashed_password: str,
    is_active: bool = True,
    is_admin: bool = False,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        next_id = _next_user_id(table.all())
        user_record = {
            "id": next_id,
            "user_uuid": str(uuid4()),
            "email": email,
            "hashed_password": hashed_password,
            "is_active": is_active,
            "is_admin": is_admin,
            "created_at": created_at,
        }
        table.insert(user_record)
        return user_record
    finally:
        db.close()


def list_user_records() -> list[dict]:
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        records = [_ensure_user_uuid(table, record) for record in table.all()]
        return sorted((_normalize_user(record) for record in records), key=lambda item: item["id"])
    finally:
        db.close()


def get_user_by_id(user_id: int) -> dict | None:
    user_query = Query()
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        record = table.get(user_query.id == user_id)
        record = _ensure_user_uuid(table, record) if record else None
        return _normalize_user(record) if record else None
    finally:
        db.close()


def get_user_by_uuid(user_uuid: str) -> dict | None:
    user_query = Query()
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        record = table.get(user_query.user_uuid == user_uuid)
        return _normalize_user(record) if record else None
    finally:
        db.close()


def get_user_by_email(email: str) -> dict | None:
    user_query = Query()
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        record = table.get(user_query.email == email)
        record = _ensure_user_uuid(table, record) if record else None
        return _normalize_user(record) if record else None
    finally:
        db.close()


def update_user_record(
    user_id: int,
    *,
    email: str,
    hashed_password: str,
    is_active: bool,
    is_admin: bool,
) -> dict | None:
    user_query = Query()
    db = get_db()
    try:
        table = db.table(USERS_TABLE)
        updated = table.update(
            {
                "email": email,
                "hashed_password": hashed_password,
                "is_active": is_active,
                "is_admin": is_admin,
            },
            user_query.id == user_id,
        )
        if not updated:
            return None
        record = table.get(user_query.id == user_id)
        return _normalize_user(record) if record else None
    finally:
        db.close()


def delete_user_record(user_id: int) -> bool:
    user_query = Query()
    db = get_db()
    try:
        removed = db.table(USERS_TABLE).remove(user_query.id == user_id)
        return bool(removed)
    finally:
        db.close()


def _next_user_id(records: list[dict]) -> int:
    if not records:
        return 1
    return max(int(record.get("id", 0)) for record in records) + 1


def _normalize_user(record: dict) -> dict:
    return {
        "id": int(record["id"]),
        "user_uuid": str(record["user_uuid"]),
        "email": record["email"],
        "hashed_password": record["hashed_password"],
        "is_active": bool(record["is_active"]),
        "is_admin": bool(record["is_admin"]),
        "created_at": record["created_at"],
    }


def _ensure_user_uuid(table, record: dict | None) -> dict | None:
    if not record:
        return record
    if record.get("user_uuid"):
        return record

    generated_uuid = str(uuid4())
    table.update({"user_uuid": generated_uuid}, Query().id == record["id"])
    record["user_uuid"] = generated_uuid
    return record
