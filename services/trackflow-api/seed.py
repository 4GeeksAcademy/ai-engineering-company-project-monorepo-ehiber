from trackflow_api.data.supplier_seed import SUPPLIERS_SEED
from trackflow_api.repositories import supplier_repository


def run_seed() -> int:
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


if __name__ == "__main__":
    run_seed()
