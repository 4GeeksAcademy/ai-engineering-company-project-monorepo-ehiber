from pathlib import Path
from functools import lru_cache
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine
from tinydb import TinyDB

from .config import get_settings


def _database_path() -> Path:
    return Path(get_settings().database_path)


def _sqlmodel_connection_uri() -> str:
    uri = get_settings().supabase_uri.strip()
    if not uri:
        raise RuntimeError("SUPABASE_URI is not configured.")
    return uri


@lru_cache
def get_inventory_engine():
    uri = _sqlmodel_connection_uri()
    connect_args = {"check_same_thread": False} if uri.startswith("sqlite") else {}
    return create_engine(uri, connect_args=connect_args)


def get_sql_session() -> Generator[Session, None, None]:
    with Session(get_inventory_engine()) as session:
        yield session


def get_db() -> TinyDB:
    db_path = _database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(db_path)


def init_tinydb() -> None:
    db = get_db()
    try:
        db.table("users")
        db.table("suppliers")
        db.table("password_reset_tokens")
        db.table("managed_incidents")
    finally:
        db.close()


def init_inventory_db() -> None:
    # Import registers SQLModel metadata for inventory entities.
    from .. import models  # noqa: F401

    SQLModel.metadata.create_all(get_inventory_engine())


def init_db() -> None:
    init_tinydb()
    init_inventory_db()
