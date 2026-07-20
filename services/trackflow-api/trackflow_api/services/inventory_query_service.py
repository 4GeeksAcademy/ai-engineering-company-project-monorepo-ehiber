"""Inventory query helpers for live agent/MCP tools (no duplicated stock math)."""

from __future__ import annotations

from sqlmodel import Session, select

from ..core.database import get_inventory_engine
from ..models import SKU, WarehouseCode
from ..routes.inventory import _build_product_reads, _compute_current_stock
from ..schemas.inventory import SKURead


def lookup_stock(*, sku_code: str | None = None, warehouse: str | None = None) -> dict:
    """Query current stock from the real inventory DB."""
    sku_code_norm = (sku_code or "").strip()
    warehouse_norm = (warehouse or "").strip().upper() or None
    warehouse_enum: WarehouseCode | None = None
    if warehouse_norm:
        try:
            warehouse_enum = WarehouseCode(warehouse_norm)
        except ValueError:
            return {
                "found": False,
                "sku": sku_code_norm or None,
                "warehouse": warehouse_norm,
                "items": [],
                "error": "invalid_warehouse",
            }

    with Session(get_inventory_engine()) as session:
        if sku_code_norm:
            statement = select(SKU).where(SKU.sku == sku_code_norm)
            if warehouse_enum is not None:
                statement = statement.where(SKU.warehouse == warehouse_enum)
            records = session.exec(statement).all()
            if not records:
                return {
                    "found": False,
                    "sku": sku_code_norm,
                    "warehouse": warehouse_norm,
                    "items": [],
                }

            items = [
                {
                    "id": record.id,
                    "name": record.name,
                    "sku": record.sku,
                    "client_name": record.client_name,
                    "category": str(
                        record.category.value if hasattr(record.category, "value") else record.category
                    ),
                    "warehouse": str(
                        record.warehouse.value if hasattr(record.warehouse, "value") else record.warehouse
                    ),
                    "current_stock": _compute_current_stock(
                        session,
                        record.id,
                        str(
                            record.warehouse.value
                            if hasattr(record.warehouse, "value")
                            else record.warehouse
                        ),
                    ),
                }
                for record in records
            ]
            return {
                "found": True,
                "sku": sku_code_norm,
                "warehouse": warehouse_norm,
                "items": items,
            }

        products: list[SKURead] = _build_product_reads(session)
        if warehouse_norm:
            products = [item for item in products if str(item.warehouse) == warehouse_norm]

        return {
            "found": bool(products),
            "sku": None,
            "warehouse": warehouse_norm,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "sku": item.sku,
                    "client_name": item.client_name,
                    "category": str(item.category),
                    "warehouse": str(item.warehouse),
                    "current_stock": item.current_stock,
                }
                for item in products[:25]
            ],
            "truncated": len(products) > 25,
        }
