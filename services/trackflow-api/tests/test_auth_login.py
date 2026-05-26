import pytest
from fastapi import HTTPException

from trackflow_api.services.auth_service import login_user, register_user


def test_login_user_happy_path():
    register_user("login@trackflow.com", "correctpass123")
    token = login_user("login@trackflow.com", "correctpass123")

    assert token.access_token
    assert token.token_type == "bearer"


def test_login_user_rejects_wrong_password():
    register_user("wrong-pass@trackflow.com", "correctpass123")

    with pytest.raises(HTTPException) as exc:
        login_user("wrong-pass@trackflow.com", "badpassword")

    assert exc.value.status_code == 401


def test_login_user_rejects_unknown_email():
    with pytest.raises(HTTPException) as exc:
        login_user("missing@trackflow.com", "anypassword123")

    assert exc.value.status_code == 401
