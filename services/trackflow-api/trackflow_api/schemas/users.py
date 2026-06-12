from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None


class UserPublic(BaseModel):
    id: int
    user_uuid: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: str


class UserInDB(UserPublic):
    hashed_password: str
