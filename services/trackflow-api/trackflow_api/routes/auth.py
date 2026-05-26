from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..core.security import get_current_user
from ..schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from ..schemas.users import UserCreate, UserPublic
from ..services.auth_service import (
    change_password,
    login_user,
    register_user,
    request_password_reset,
    reset_password_with_token,
)


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    return login_user(form_data.username, form_data.password)


@router.post("/register", response_model=TokenResponse)
async def register(payload: UserCreate) -> TokenResponse:
    _, token = register_user(payload.email, payload.password)
    return token


@router.get("/me", response_model=UserPublic)
async def me(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    return current_user


@router.post("/change-password", status_code=204)
async def change_password_route(
    payload: ChangePasswordRequest,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> None:
    change_password(current_user.id, payload.current_password, payload.new_password)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password_route(payload: ForgotPasswordRequest) -> MessageResponse:
    message = request_password_reset(payload.email)
    return MessageResponse(message=message)


@router.post("/reset-password", status_code=204)
async def reset_password_route(payload: ResetPasswordRequest) -> None:
    reset_password_with_token(payload.token, payload.new_password)
