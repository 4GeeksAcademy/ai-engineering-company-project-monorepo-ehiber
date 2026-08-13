from uuid import uuid4

from fastapi.testclient import TestClient

from trackflow_api.core.security import create_access_token, get_password_hash
from trackflow_api.repositories.user_repository import create_user_record


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _user_headers(client: TestClient) -> dict[str, str]:
    email = f"member-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    record = create_user_record(
        email=f"admin-{uuid4().hex[:8]}@trackflow.com",
        hashed_password=get_password_hash("securepass123"),
        is_admin=True,
    )
    token = create_access_token(record["user_uuid"])
    return {"Authorization": f"Bearer {token}"}


def test_create_user_requires_authentication():
    response = _client().post(
        "/users",
        json={"email": f"open-{uuid4().hex[:8]}@trackflow.com", "password": "securepass123"},
    )
    assert response.status_code == 401


def test_list_users_requires_authentication():
    response = _client().get("/users")
    assert response.status_code == 401


def test_list_users_forbidden_for_non_admin():
    client = _client()
    headers = _user_headers(client)
    response = client.get("/users", headers=headers)
    assert response.status_code == 403


def test_create_user_forbidden_for_non_admin():
    client = _client()
    headers = _user_headers(client)
    response = client.post(
        "/users",
        headers=headers,
        json={"email": f"blocked-{uuid4().hex[:8]}@trackflow.com", "password": "securepass123"},
    )
    assert response.status_code == 403


def test_admin_can_list_and_create_users():
    client = _client()
    headers = _admin_headers()
    listed = client.get("/users", headers=headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)

    email = f"provisioned-{uuid4().hex[:8]}@trackflow.com"
    created = client.post(
        "/users",
        headers=headers,
        json={"email": email, "password": "securepass123"},
    )
    assert created.status_code == 201
    assert created.json()["email"] == email
    assert created.json()["is_admin"] is False
