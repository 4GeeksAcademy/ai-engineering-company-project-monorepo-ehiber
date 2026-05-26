import pytest
from fastapi import HTTPException

from trackflow_api.services.auth_service import register_user


def test_register_user_happy_path():
    user, token = register_user("student@trackflow.com", "securepass123")

    assert user["email"] == "student@trackflow.com"
    assert token.access_token
    assert token.token_type == "bearer"


def test_register_user_rejects_duplicate_email():
    register_user("duplicate@trackflow.com", "securepass123")

    with pytest.raises(HTTPException) as exc:
        register_user("duplicate@trackflow.com", "anotherpass123")

    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


def test_register_user_rejects_empty_password():
    with pytest.raises(HTTPException) as exc:
        register_user("empty-pass@trackflow.com", "")

    assert exc.value.status_code == 400
