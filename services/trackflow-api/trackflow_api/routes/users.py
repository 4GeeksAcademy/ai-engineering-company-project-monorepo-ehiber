from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from ..core.security import ensure_user_or_admin, get_current_admin, get_current_user
from ..schemas.users import UserCreate, UserListItem, UserPublic, UserUpdate
from ..services.user_service import create_user, delete_user, get_user, list_users, update_user


router = APIRouter()


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: UserCreate,
    current_user: Annotated[UserPublic, Depends(get_current_admin)],
) -> UserPublic:
    _ = current_user
    return UserPublic.model_validate(create_user(email=payload.email, password=payload.password))


@router.get("", response_model=list[UserListItem])
async def list_users_route(
    current_user: Annotated[UserPublic, Depends(get_current_admin)],
) -> list[UserListItem]:
    users = list_users()
    return [
        UserListItem(
            id=user["id"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_route(
    user_id: int,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    ensure_user_or_admin(current_user, user_id)
    return UserPublic.model_validate(get_user(user_id))


@router.put("/{user_id}", response_model=UserPublic)
async def update_user_route(
    user_id: int,
    payload: UserUpdate,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    ensure_user_or_admin(current_user, user_id)
    return UserPublic.model_validate(update_user(user_id, payload))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    user_id: int,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> Response:
    ensure_user_or_admin(current_user, user_id)
    delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
