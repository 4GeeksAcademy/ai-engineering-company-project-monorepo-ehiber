from uuid import uuid4

from fastapi.testclient import TestClient


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"suppliers-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


_SUPPLIER_PAYLOAD = {
    "name": "Pacific Freight",
    "country": "USA",
    "categories": ["carrier_last_mile"],
    "rate_per_shipment": 12.5,
    "status": "active",
}


def test_suppliers_list_requires_authentication():
    response = _client().get("/suppliers")
    assert response.status_code == 401


def test_suppliers_create_requires_authentication():
    response = _client().post("/suppliers", json=_SUPPLIER_PAYLOAD)
    assert response.status_code == 401


def test_suppliers_list_ok_when_authenticated():
    client = _client()
    headers = _auth_headers(client)
    response = client.get("/suppliers", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_suppliers_create_ok_when_authenticated():
    client = _client()
    headers = _auth_headers(client)
    response = client.post("/suppliers", headers=headers, json=_SUPPLIER_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["name"] == "Pacific Freight"
