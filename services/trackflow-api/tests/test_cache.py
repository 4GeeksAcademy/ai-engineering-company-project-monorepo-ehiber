from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from trackflow_api.core.cache import INVENTORY_PRODUCTS_KEY, cache_clear, cache_get, cache_set
from trackflow_api.services.incident_manager_service import create_incident, get_incident_summary
from trackflow_api.schemas.incidents_manager import IncidentCreate
from trackflow_api.services.supplier_service import create_supplier, list_suppliers
from trackflow_api.schemas.suppliers import SupplierCategory, SupplierCountry, SupplierCreate, SupplierStatus


@pytest.fixture(autouse=True)
def clear_app_cache():
    cache_clear()
    yield
    cache_clear()


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"cache-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_inventory_products_cache_is_invalidated_after_inbound():
    client = _client()
    headers = _auth_headers(client)

    product_response = client.post(
        "/inventory/products",
        headers=headers,
        json={
            "name": "Cache Test Hoodie",
            "sku": "CLT-HDY-001",
            "client_name": "ModaSprint",
            "category": "fashion",
            "warehouse": "LA",
        },
    )
    assert product_response.status_code == 201
    sku_id = product_response.json()["id"]

    first = client.get("/inventory/products")
    second = client.get("/inventory/products")
    assert first.status_code == 200
    assert second.status_code == 200
    assert cache_get(INVENTORY_PRODUCTS_KEY) is not None

    inbound_response = client.post(
        "/inventory/orders/inbound",
        headers=headers,
        json={
            "sku_id": sku_id,
            "quantity": 10,
            "reference": "CACHE-TEST-001",
            "warehouse": "LA",
        },
    )
    assert inbound_response.status_code == 201
    assert cache_get(INVENTORY_PRODUCTS_KEY) is None

    refreshed = client.get("/inventory/products").json()
    product = next(item for item in refreshed if item["id"] == sku_id)
    assert product["current_stock"] == 10


def test_suppliers_list_cache_is_invalidated_after_create():
    cache_set("suppliers:list:country=*:category=*", [{"id": 1}], ttl_seconds=60)
    assert cache_get("suppliers:list:country=*:category=*") is not None

    create_supplier(
        SupplierCreate(
            name="Cache Supplier",
            country=SupplierCountry.USA,
            categories=[SupplierCategory.CARRIER_LAST_MILE],
            rate_per_shipment=9.5,
            status=SupplierStatus.ACTIVE,
        )
    )

    assert cache_get("suppliers:list:country=*:category=*") is None
    suppliers = list_suppliers()
    assert any(supplier.name == "Cache Supplier" for supplier in suppliers)


def test_incident_summary_cache_is_invalidated_after_create():
    first = get_incident_summary()
    second = get_incident_summary()
    assert first.total == second.total

    create_incident(
        IncidentCreate(
            title="Cache invalidation incident",
            description="Created to verify summary cache busting.",
            category="lost_parcel",
            origin="customer",
            branch="central",
        )
    )

    updated = get_incident_summary()
    assert updated.total == first.total + 1
