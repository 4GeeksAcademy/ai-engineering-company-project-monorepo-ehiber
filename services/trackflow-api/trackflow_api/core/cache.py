from time import monotonic
from typing import Any

_store: dict[str, tuple[float, Any]] = {}

INVENTORY_PREFIX = "inventory:"
INVENTORY_PRODUCTS_KEY = f"{INVENTORY_PREFIX}products"
INVENTORY_ORDERS_KEY = f"{INVENTORY_PREFIX}orders"
INCIDENTS_SUMMARY_KEY = "incidents:summary"
SUPPLIERS_LIST_PREFIX = "suppliers:list:"
TELEMETRY_PREFIX = "telemetry:"
TELEMETRY_REPORT_KEY = f"{TELEMETRY_PREFIX}report"


def cache_get(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None

    expires_at, value = entry
    if monotonic() >= expires_at:
        del _store[key]
        return None

    return value


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    _store[key] = (monotonic() + ttl_seconds, value)


def cache_invalidate_prefix(prefix: str) -> None:
    keys_to_delete = [key for key in _store if key.startswith(prefix)]
    for key in keys_to_delete:
        del _store[key]


def cache_clear() -> None:
    _store.clear()


def suppliers_list_cache_key(*, country: str | None, category: str | None) -> str:
    return f"{SUPPLIERS_LIST_PREFIX}country={country or '*'}:category={category or '*'}"
