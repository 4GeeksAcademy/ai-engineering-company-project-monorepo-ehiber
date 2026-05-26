import secrets
from datetime import datetime, timedelta, timezone

from tinydb import Query

from ..core.database import get_db


RESET_TOKENS_TABLE = "password_reset_tokens"


def create_reset_token(user_id: int, expires_minutes: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).isoformat()
    db = get_db()
    try:
        table = db.table(RESET_TOKENS_TABLE)
        table.insert(
            {
                "token": token,
                "user_id": user_id,
                "expires_at": expires_at,
                "used": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return token
    finally:
        db.close()


def get_valid_reset_token(token: str) -> dict | None:
    token_query = Query()
    db = get_db()
    try:
        record = db.table(RESET_TOKENS_TABLE).get(token_query.token == token)
        if not record or record.get("used"):
            return None

        expires_at = datetime.fromisoformat(record["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None

        return {
            "token": record["token"],
            "user_id": int(record["user_id"]),
            "expires_at": record["expires_at"],
            "used": bool(record["used"]),
        }
    finally:
        db.close()


def mark_reset_token_used(token: str) -> None:
    token_query = Query()
    db = get_db()
    try:
        db.table(RESET_TOKENS_TABLE).update({"used": True}, token_query.token == token)
    finally:
        db.close()
