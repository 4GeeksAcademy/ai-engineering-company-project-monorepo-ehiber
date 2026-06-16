from trackflow_api.data.supplier_seed import SUPPLIERS_SEED
from trackflow_api.data.inventory_seed import (
    INVENTORY_INBOUND_SEED,
    INVENTORY_OUTBOUND_SEED,
    INVENTORY_PRODUCTS_SEED,
)
from sqlmodel import Session, select

from trackflow_api.core.database import get_inventory_engine
from trackflow_api.models import ExitType, SKU, SKUCategory, StockEntry, StockExit, WarehouseCode
from trackflow_api.repositories import supplier_repository


def run_supplier_seed() -> int:
    inserted = 0
    for supplier in SUPPLIERS_SEED:
        existing = supplier_repository.get_supplier_by_name_and_country(
            supplier["name"],
            supplier["country"],
        )
        if existing:
            continue

        supplier_repository.create_supplier_record(
            {
                **supplier,
                "rate_updated_at": supplier_repository.current_timestamp(),
            }
        )
        inserted += 1

    print(f"Supplier seed complete. Inserted {inserted} new records.")
    return inserted


def run_inventory_seed() -> dict[str, int]:
    inserted = {
        "products": 0,
        "inbound": 0,
        "outbound": 0,
    }

    with Session(get_inventory_engine()) as session:
        sku_by_key: dict[tuple[str, str], SKU] = {}

        for product in INVENTORY_PRODUCTS_SEED:
            sku_code = str(product["sku"])
            warehouse_code = str(product["warehouse"])
            existing = session.exec(
                select(SKU).where(
                    SKU.sku == sku_code,
                    SKU.warehouse == WarehouseCode(warehouse_code),
                )
            ).first()

            if existing is None:
                existing = SKU(
                    name=str(product["name"]),
                    sku=sku_code,
                    client_name=str(product["client_name"]),
                    category=SKUCategory(str(product["category"])),
                    warehouse=WarehouseCode(warehouse_code),
                )
                session.add(existing)
                session.flush()
                inserted["products"] += 1

            sku_by_key[(sku_code, warehouse_code)] = existing

        for movement in INVENTORY_INBOUND_SEED:
            sku_code = str(movement["sku"])
            warehouse_code = str(movement["warehouse"])
            reference = str(movement["reference"])
            sku = sku_by_key.get((sku_code, warehouse_code))
            if sku is None:
                continue

            existing_entry = session.exec(
                select(StockEntry).where(
                    StockEntry.sku_id == sku.id,
                    StockEntry.reference == reference,
                )
            ).first()
            if existing_entry is not None:
                continue

            session.add(
                StockEntry(
                    sku_id=sku.id,
                    quantity=int(movement["quantity"]),
                    reference=reference,
                    warehouse=WarehouseCode(warehouse_code),
                    user_uuid="seed-system",
                )
            )
            inserted["inbound"] += 1

        for movement in INVENTORY_OUTBOUND_SEED:
            sku_code = str(movement["sku"])
            warehouse_code = str(movement["warehouse"])
            tracking_number = movement.get("tracking_number")
            sku = sku_by_key.get((sku_code, warehouse_code))
            if sku is None:
                continue

            existing_exit = session.exec(
                select(StockExit).where(
                    StockExit.sku_id == sku.id,
                    StockExit.exit_type == ExitType(str(movement["exit_type"])),
                    StockExit.quantity == int(movement["quantity"]),
                    StockExit.tracking_number == tracking_number,
                )
            ).first()
            if existing_exit is not None:
                continue

            session.add(
                StockExit(
                    sku_id=sku.id,
                    quantity=int(movement["quantity"]),
                    exit_type=ExitType(str(movement["exit_type"])),
                    tracking_number=tracking_number,
                    warehouse=WarehouseCode(warehouse_code),
                    user_uuid="seed-system",
                )
            )
            inserted["outbound"] += 1

        session.commit()

    print(
        "Inventory seed complete. "
        f"Inserted products={inserted['products']}, "
        f"inbound={inserted['inbound']}, "
        f"outbound={inserted['outbound']}."
    )
    return inserted


def run_seed() -> int:
    supplier_inserted = run_supplier_seed()
    inventory_inserted = run_inventory_seed()
    return supplier_inserted + sum(inventory_inserted.values())


if __name__ == "__main__":
    run_seed()
