from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..repositories.user_repository import get_user_by_id
from ..schemas.auth import TokenPayload
from ..schemas.users import UserPublic
from .config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("TRACKFLOW_JWT_SECRET_KEY is not configured.")

    expire_window = expires_minutes or settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_window)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("TRACKFLOW_JWT_SECRET_KEY is not configured.")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise _credentials_exception()
        return TokenPayload(sub=subject)
    except JWTError as exc:
        raise _credentials_exception() from exc


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserPublic:
    token_payload = decode_access_token(token)
    if not token_payload.sub.isdigit():
        raise _credentials_exception()

    user_record = get_user_by_id(int(token_payload.sub))
    if not user_record or not user_record["is_active"]:
        raise _credentials_exception()

    return UserPublic.model_validate(user_record)


def ensure_user_or_admin(current_user: UserPublic, user_id: int) -> None:
    if current_user.is_admin or current_user.id == user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to access this resource.",
    )


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
