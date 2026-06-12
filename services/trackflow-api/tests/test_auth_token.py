import pytest
from fastapi import HTTPException

from trackflow_api.core.security import create_access_token, decode_access_token, verify_password, get_password_hash
from trackflow_api.services.auth_service import register_user


def test_create_and_decode_access_token():
    user, _ = register_user("token@trackflow.com", "securepass123")
    token = create_access_token(user["user_uuid"])
    payload = decode_access_token(token)

    assert payload.sub == user["user_uuid"]


def test_decode_access_token_rejects_malformed_token():
    with pytest.raises(HTTPException) as exc:
        decode_access_token("not-a-valid-token")

    assert exc.value.status_code == 401


def test_password_hash_roundtrip():
    hashed = get_password_hash("my-secret-password")
    assert verify_password("my-secret-password", hashed) is True
    assert verify_password("wrong-password", hashed) is False
