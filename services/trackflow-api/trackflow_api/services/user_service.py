from fastapi import HTTPException

from ..core.security import get_password_hash
from ..repositories.user_repository import (
    create_user_record,
    delete_user_record,
    get_user_by_email,
    get_user_by_id,
    list_user_records,
    update_user_record,
)
from ..schemas.users import UserUpdate


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_user(*, email: str, password: str) -> dict:
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    existing_user = get_user_by_email(normalized_email)
    if existing_user:
        raise HTTPException(status_code=400, detail="A user with this email already exists.")

    return create_user_record(
        email=normalized_email,
        hashed_password=get_password_hash(password),
    )


def list_users() -> list[dict]:
    return list_user_records()


def get_user(user_id: int) -> dict:
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def update_user(user_id: int, payload: UserUpdate) -> dict:
    existing_user = get_user(user_id)
    new_email = normalize_email(payload.email) if payload.email is not None else existing_user["email"]
    if not new_email:
        raise HTTPException(status_code=400, detail="Email cannot be empty.")

    if new_email != existing_user["email"]:
        same_email_user = get_user_by_email(new_email)
        if same_email_user and same_email_user["id"] != user_id:
            raise HTTPException(status_code=400, detail="A user with this email already exists.")

    hashed_password = existing_user["hashed_password"]
    if payload.password is not None:
        if not payload.password:
            raise HTTPException(status_code=400, detail="Password cannot be empty.")
        hashed_password = get_password_hash(payload.password)

    is_active = existing_user["is_active"] if payload.is_active is None else payload.is_active

    return update_user_record(
        user_id,
        email=new_email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_admin=existing_user["is_admin"],
    )


def delete_user(user_id: int) -> None:
    deleted = delete_user_record(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
