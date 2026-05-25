from fastapi import HTTPException, status

from ..core.security import create_access_token, verify_password
from ..repositories.user_repository import get_user_by_email
from ..schemas.auth import TokenResponse
from ..schemas.users import UserInDB
from .user_service import create_user, normalize_email


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


def _invalid_credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )
