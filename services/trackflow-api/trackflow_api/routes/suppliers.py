from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.security import get_current_user

from ..schemas.suppliers import (
    SupplierCategory,
    SupplierCountry,
    SupplierCreate,
    SupplierListItem,
    SupplierPublic,
    SupplierRateUpdate,
    SupplierStatusUpdate,
)
from ..services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_supplier,
    list_suppliers,
    update_supplier_rate,
    update_supplier_status,
)


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=SupplierPublic, status_code=201)
async def create_supplier_route(payload: SupplierCreate) -> SupplierPublic:
    return create_supplier(payload)


@router.get("", response_model=list[SupplierListItem])
async def list_suppliers_route(
    country: SupplierCountry | None = Query(default=None),
    category: SupplierCategory | None = Query(default=None),
) -> list[SupplierListItem]:
    suppliers = list_suppliers(
        country=country.value if country else None,
        category=category.value if category else None,
    )
    
    return [
        SupplierListItem(
            id=supplier.id,
            name=supplier.name,
            country=supplier.country,
            status=supplier.status,
            categories=supplier.categories
        )
        for supplier in suppliers
    ]


@router.get("/{supplier_id}", response_model=SupplierPublic)
async def get_supplier_route(supplier_id: int) -> SupplierPublic:
    supplier = get_supplier(supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier


@router.patch("/{supplier_id}/rate", response_model=SupplierPublic)
async def update_supplier_rate_route(
    supplier_id: int,
    payload: SupplierRateUpdate,
) -> SupplierPublic:
    supplier = update_supplier_rate(supplier_id, payload)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier


@router.patch("/{supplier_id}/status", response_model=SupplierPublic)
async def update_supplier_status_route(
    supplier_id: int,
    payload: SupplierStatusUpdate,
) -> SupplierPublic:
    supplier = update_supplier_status(supplier_id, payload)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier_route(supplier_id: int) -> None:
    deleted = delete_supplier(supplier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Supplier not found.")
