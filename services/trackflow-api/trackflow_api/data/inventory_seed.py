INVENTORY_PRODUCTS_SEED = [
    {
        "name": "Performance Running Shoes",
        "sku": "CLT-RUN-001",
        "client_name": "ModaSprint",
        "category": "fashion",
        "warehouse": "LA",
    },
    {
        "name": "Compression Sports Leggings",
        "sku": "CLT-LEG-014",
        "client_name": "ModaSprint",
        "category": "fashion",
        "warehouse": "ZGZ",
    },
    {
        "name": "Wireless Earbuds Pro",
        "sku": "TEC-EAR-009",
        "client_name": "ElectroHub",
        "category": "electronics",
        "warehouse": "LA",
    },
    {
        "name": "65W GaN Fast Charger",
        "sku": "TEC-CHG-065",
        "client_name": "ElectroHub",
        "category": "electronics",
        "warehouse": "ZGZ",
    },
    {
        "name": "Vitamin C Glow Serum",
        "sku": "CSM-SRM-030",
        "client_name": "FreshBox",
        "category": "cosmetics",
        "warehouse": "LA",
    },
]

INVENTORY_INBOUND_SEED = [
    {
        "sku": "CLT-RUN-001",
        "warehouse": "LA",
        "quantity": 120,
        "reference": "SEED-IN-CLT-RUN-001-LA",
    },
    {
        "sku": "CLT-LEG-014",
        "warehouse": "ZGZ",
        "quantity": 85,
        "reference": "SEED-IN-CLT-LEG-014-ZGZ",
    },
    {
        "sku": "TEC-EAR-009",
        "warehouse": "LA",
        "quantity": 200,
        "reference": "SEED-IN-TEC-EAR-009-LA",
    },
    {
        "sku": "TEC-CHG-065",
        "warehouse": "ZGZ",
        "quantity": 150,
        "reference": "SEED-IN-TEC-CHG-065-ZGZ",
    },
    {
        "sku": "CSM-SRM-030",
        "warehouse": "LA",
        "quantity": 95,
        "reference": "SEED-IN-CSM-SRM-030-LA",
    },
]

INVENTORY_OUTBOUND_SEED = [
    {
        "sku": "CLT-RUN-001",
        "warehouse": "LA",
        "quantity": 12,
        "exit_type": "dispatch",
        "tracking_number": "TF-SEED-OUT-1001",
    },
    {
        "sku": "TEC-EAR-009",
        "warehouse": "LA",
        "quantity": 10,
        "exit_type": "dispatch",
        "tracking_number": "TF-SEED-OUT-1002",
    },
    {
        "sku": "CSM-SRM-030",
        "warehouse": "LA",
        "quantity": 3,
        "exit_type": "loss",
        "tracking_number": None,
    },
]
