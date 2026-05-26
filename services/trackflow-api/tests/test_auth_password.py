import pytest
from fastapi import HTTPException

from trackflow_api.services.auth_service import (
    change_password,
    login_user,
    register_user,
    request_password_reset,
    reset_password_with_token,
)


def test_change_password_happy_path():
    user, _ = register_user("password@trackflow.com", "oldpass123")
    change_password(user["id"], "oldpass123", "newpass456")
    token = login_user("password@trackflow.com", "newpass456")

    assert token.access_token


def test_change_password_rejects_wrong_current_password():
    user, _ = register_user("bad-current@trackflow.com", "oldpass123")

    with pytest.raises(HTTPException) as exc:
        change_password(user["id"], "wrong-current", "newpass456")

    assert exc.value.status_code == 400


def test_password_reset_flow_happy_path():
    register_user("reset@trackflow.com", "oldpass123")
    message = request_password_reset("reset@trackflow.com")

    assert "password reset link" in message.lower()

    from pathlib import Path
    from trackflow_api.core.config import get_settings
    from urllib.parse import parse_qs, urlparse

    text = Path(get_settings().dev_email_output_dir, "last_password_reset.txt").read_text(encoding="utf-8")
    reset_url = text.split("Reset URL: ")[1].strip()
    token = parse_qs(urlparse(reset_url).query)["token"][0]

    reset_password_with_token(token, "newpass456")
    token_response = login_user("reset@trackflow.com", "newpass456")

    assert token_response.access_token


def test_password_reset_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        reset_password_with_token("invalid-token-value", "newpass456")

    assert exc.value.status_code == 400
