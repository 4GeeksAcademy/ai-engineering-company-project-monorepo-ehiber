import json
from pathlib import Path

from ...core.config import get_settings
from ...core.errors import AnalysisInputError


DEFAULT_MANAGER_CONTEXT = {
    "branches": [
        "central",
        "la_warehouse",
        "la_office",
        "zaragoza_warehouse",
        "zaragoza_office",
    ],
    "branch_labels": {
        "central": "Central",
        "la_warehouse": "Los Angeles - Warehouse",
        "la_office": "Los Angeles - Office",
        "zaragoza_warehouse": "Zaragoza - Warehouse",
        "zaragoza_office": "Zaragoza - Office",
    },
    "categories": [
        "lost_parcel",
        "delivery_failure",
        "inventory_discrepancy",
        "carrier_issue",
        "returns_issue",
        "warehouse_incident",
        "system_failure",
        "client_complaint",
        "other",
    ],
    "statuses": ["open", "in_progress", "resolved", "discarded"],
    "origins": ["customer", "branch", "internal"],
    "status_transitions": {
        "open": ["in_progress", "discarded"],
        "in_progress": ["resolved", "discarded"],
    },
}


def load_manager_context(config_path: str | Path | None = None) -> dict:
    path = Path(config_path or get_settings().incidents_manager_context_path)
    if not path.exists():
        return DEFAULT_MANAGER_CONTEXT

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AnalysisInputError(f"Invalid incident manager context JSON: {path}") from exc
