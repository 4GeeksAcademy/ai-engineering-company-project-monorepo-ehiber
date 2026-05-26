import pytest
from fastapi import HTTPException

from trackflow_api.schemas.suppliers import SupplierCreate, SupplierCountry, SupplierCategory, SupplierStatus
from trackflow_api.services.incident_manager_service import FieldValidationError, create_incident, update_incident_status
from trackflow_api.schemas.incidents_manager import IncidentCreate, IncidentStatusUpdate
from trackflow_api.services.supplier_service import create_supplier, get_supplier


def test_create_supplier_happy_path():
    supplier = create_supplier(
        SupplierCreate(
            name="Pacific Freight",
            country=SupplierCountry.USA,
            categories=[SupplierCategory.CARRIER_LAST_MILE],
            rate_per_shipment=12.5,
            status=SupplierStatus.ACTIVE,
        )
    )

    assert supplier.name == "Pacific Freight"
    assert get_supplier(supplier.id) is not None


def test_create_supplier_rejects_invalid_rate():
    with pytest.raises(Exception):
        create_supplier(
            SupplierCreate(
                name="Bad Rate Supplier",
                country=SupplierCountry.USA,
                categories=[SupplierCategory.CARRIER_LAST_MILE],
                rate_per_shipment=0,
                status=SupplierStatus.ACTIVE,
            )
        )


def test_incident_status_transition_validation():
    incident = create_incident(
        IncidentCreate(
            title="Lost parcel in LA hub",
            description="Parcel missing after inbound scan.",
            category="lost_parcel",
            origin="customer",
            branch="central",
        )
    )

    updated = update_incident_status(incident.id, IncidentStatusUpdate(status="in_progress"))
    assert updated.status == "in_progress"

    with pytest.raises(FieldValidationError):
        update_incident_status(incident.id, IncidentStatusUpdate(status="open"))
