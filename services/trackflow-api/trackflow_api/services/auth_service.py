from fastapi import HTTPException, status

from ..core.security import create_access_token, verify_password
from ..core.config import get_settings
from ..repositories.password_reset_repository import (
    create_reset_token,
    get_valid_reset_token,
    mark_reset_token_used,
)
from ..repositories.user_repository import get_user_by_email
from ..schemas.auth import TokenResponse
from ..schemas.users import UserInDB, UserUpdate
from .email_service import EmailDeliveryError, send_password_reset_email
from .user_service import create_user, get_user, normalize_email, update_user


def login_user(email: str, password: str) -> TokenResponse:
    user_record = get_user_by_email(normalize_email(email))
    if not user_record:
        raise _invalid_credentials_error()

    user = UserInDB.model_validate(user_record)
    if not verify_password(password, user.hashed_password):
        raise _invalid_credentials_error()

    return TokenResponse(access_token=create_access_token(user.id))


def register_user(email: str, password: str) -> tuple[dict, TokenResponse]:
    user = create_user(email=email, password=password)
    return user, TokenResponse(access_token=create_access_token(user["id"]))


def change_password(user_id: int, current_password: str, new_password: str) -> None:
    user_record = get_user(user_id)
    user = UserInDB.model_validate(user_record)
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    update_user(user_id, UserUpdate(password=new_password))


FORGOT_PASSWORD_MESSAGE = (
    "If that address is registered, you will receive a password reset link shortly."
)


def request_password_reset(email: str) -> str:
    normalized_email = normalize_email(email)
    user_record = get_user_by_email(normalized_email)
    if not user_record:
        return FORGOT_PASSWORD_MESSAGE

    settings = get_settings()
    token = create_reset_token(
        int(user_record["id"]),
        settings.password_reset_expire_minutes,
    )
    reset_url = f"{settings.password_reset_app_url}/reset-password?token={token}"

    try:
        send_password_reset_email(recipient=normalized_email, reset_url=reset_url)
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to send password reset email at this time.",
        ) from exc

    return FORGOT_PASSWORD_MESSAGE


def reset_password_with_token(token: str, new_password: str) -> None:
    reset_record = get_valid_reset_token(token)
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    update_user(reset_record["user_id"], UserUpdate(password=new_password))
    mark_reset_token_used(token)


def _invalid_credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )
