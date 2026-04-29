from datetime import datetime, timezone

from ..core.database import get_db_connection


def create_user_record(
    *,
    email: str,
    hashed_password: str,
    is_active: bool = True,
    is_admin: bool = False,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (email, hashed_password, is_active, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, hashed_password, int(is_active), int(is_admin), created_at),
        )
        return get_user_by_id(cursor.lastrowid)


def list_user_records() -> list[dict]:
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, email, hashed_password, is_active, is_admin, created_at
            FROM users
            ORDER BY id ASC
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_user_by_id(user_id: int) -> dict | None:
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, hashed_password, is_active, is_admin, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, email, hashed_password, is_active, is_admin, created_at
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def update_user_record(
    user_id: int,
    *,
    email: str,
    hashed_password: str,
    is_active: bool,
    is_admin: bool,
) -> dict | None:
    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET email = ?, hashed_password = ?, is_active = ?, is_admin = ?
            WHERE id = ?
            """,
            (email, hashed_password, int(is_active), int(is_admin), user_id),
        )
    return get_user_by_id(user_id)


def delete_user_record(user_id: int) -> bool:
    with get_db_connection() as connection:
        cursor = connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cursor.rowcount > 0


def _row_to_dict(row) -> dict:
    return {
        "id": int(row["id"]),
        "email": row["email"],
        "hashed_password": row["hashed_password"],
        "is_active": bool(row["is_active"]),
        "is_admin": bool(row["is_admin"]),
        "created_at": row["created_at"],
    }
