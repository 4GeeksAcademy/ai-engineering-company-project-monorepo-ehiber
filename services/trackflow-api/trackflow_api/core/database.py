from pathlib import Path

from tinydb import TinyDB

from .config import get_settings


def _database_path() -> Path:
    return Path(get_settings().database_path)


def get_db() -> TinyDB:
    db_path = _database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(db_path)


def init_db() -> None:
    db = get_db()
    try:
        db.table("users")
    finally:
        db.close()
