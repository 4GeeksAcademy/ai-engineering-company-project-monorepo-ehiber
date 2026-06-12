from uuid import uuid4

from fastapi.testclient import TestClient


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"inventory-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_inventory_products_get_is_public():
    client = _client()

    response = client.get("/inventory/products")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_inventory_products_post_requires_authentication():
    client = _client()

    response = client.post(
        "/inventory/products",
        json={
            "name": "Classic White Sneaker - Size 42",
            "sku": "CLT-SNK-W-42",
            "client_name": "PureStep Footwear",
            "category": "fashion",
            "warehouse": "LA",
        },
    )

    assert response.status_code == 401


def test_outbound_dispatch_requires_tracking_number():
    client = _client()
    headers = _auth_headers(client)

    product_response = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "Wireless Earbuds Pro",
            "sku": "TEC-EAR-001",
            "client_name": "SoundWave Electronics",
            "category": "electronics",
            "warehouse": "LA",
        },
    )
    sku_id = product_response.json()["id"]

    inbound_response = client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": sku_id,
            "quantity": 8,
            "reference": "PO-2024-0098",
            "warehouse": "LA",
        },
    )
    assert inbound_response.status_code == 201

    response = client.post(
        "/inventory/orders/outbound",
        headers=headers,
        json={
            "sku_id": sku_id,
            "quantity": 3,
            "exit_type": "dispatch",
            "warehouse": "LA",
        },
    )

    assert response.status_code == 400


def test_outbound_loss_rejects_tracking_number():
    client = _client()
    headers = _auth_headers(client)

    product_response = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "USB-C Fast Charger 65W",
            "sku": "TEC-CHG-065",
            "client_name": "SoundWave Electronics",
            "category": "electronics",
            "warehouse": "ZGZ",
        },
    )
    sku_id = product_response.json()["id"]

    inbound_response = client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": sku_id,
            "quantity": 8,
            "reference": "PO-2024-0123",
            "warehouse": "ZGZ",
        },
    )
    assert inbound_response.status_code == 201

    response = client.post(
        "/inventory/orders/outbound",
        headers=headers,
        json={
            "sku_id": sku_id,
            "quantity": 2,
            "exit_type": "loss",
            "tracking_number": "1Z999AA10123456784",
            "warehouse": "ZGZ",
        },
    )

    assert response.status_code == 400


def test_outbound_rejects_insufficient_stock_with_exact_message():
    client = _client()
    headers = _auth_headers(client)

    product_response = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "Hydrating Face Serum 30ml",
            "sku": "CSM-SRM-030",
            "client_name": "GlowLab Cosmetics",
            "category": "cosmetics",
            "warehouse": "ZGZ",
        },
    )
    sku_payload = product_response.json()

    inbound_response = client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": sku_payload["id"],
            "quantity": 5,
            "reference": "GR-ZGZ-0234",
            "warehouse": "ZGZ",
        },
    )
    assert inbound_response.status_code == 201

    response = client.post(
        "/inventory/orders/outbound",
        headers=headers,
        json={
            "sku_id": sku_payload["id"],
            "quantity": 9,
            "exit_type": "loss",
            "tracking_number": None,
            "warehouse": "ZGZ",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Insufficient stock for SKU 'CSM-SRM-030'. Available: 5, requested: 9."
    )


def test_current_stock_is_computed_per_warehouse():
    client = _client()
    headers = _auth_headers(client)

    la_product = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "Classic White Sneaker - Size 42",
            "sku": "CLT-SNK-W-42",
            "client_name": "PureStep Footwear",
            "category": "fashion",
            "warehouse": "LA",
        },
    ).json()

    zgz_product = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "Classic White Sneaker - Size 42",
            "sku": "CLT-SNK-W-42",
            "client_name": "PureStep Footwear",
            "category": "fashion",
            "warehouse": "ZGZ",
        },
    ).json()

    client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": la_product["id"],
            "quantity": 20,
            "reference": "GR-LA-0001",
            "warehouse": "LA",
        },
    )
    client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": zgz_product["id"],
            "quantity": 15,
            "reference": "GR-ZGZ-0001",
            "warehouse": "ZGZ",
        },
    )

    la_data = client.get(f"/inventory/products/{la_product['id']}").json()
    zgz_data = client.get(f"/inventory/products/{zgz_product['id']}").json()

    assert la_data["warehouse"] == "LA"
    assert la_data["current_stock"] == 20
    assert zgz_data["warehouse"] == "ZGZ"
    assert zgz_data["current_stock"] == 15
