from __future__ import annotations

import sys
from pathlib import Path

from sqlmodel import Session

_SERVICES_API = Path(__file__).resolve().parents[4] / "services" / "trackflow-api"
_SERVICES = Path(__file__).resolve().parents[4] / "services"
for path in (_SERVICES_API, _SERVICES):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from trackflow_api.core.database import get_inventory_engine, init_inventory_db  # noqa: E402


def get_session() -> Session:
    init_inventory_db()
    return Session(get_inventory_engine())
