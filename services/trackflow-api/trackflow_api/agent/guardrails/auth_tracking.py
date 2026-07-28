from __future__ import annotations

import re
from typing import Callable

from .types import TrackingAuthResult

OwnerLookup = Callable[[str], str | None]

_TRACKING_REQUEST_HINTS = (
    r"\bpedido\b",
    r"\border\b",
    r"\btracking\b",
    r"\benv[ií]o\b",
    r"\bshipment\b",
    r"\bpaquete\b",
    r"\bparcel\b",
)

_TRACKING_ID_PATTERNS = (
    r"(?:pedido|order|tracking|env[ií]o|shipment)\s*[#:.-]?\s*([A-Za-z0-9_-]{4,})",
    r"#\s*([A-Za-z0-9_-]{4,})",
    r"\b(TF-[A-Z0-9-]+)\b",
)


def extract_tracking_id(question: str) -> str | None:
    """Extract a shipment/order id only when the question is about tracking.

    SKU-looking tokens (e.g. TF-ELEC-0010 in inventory questions) are ignored
    unless the user also used pedido/tracking/envío wording.
    """
    text = (question or "").strip()
    if not text:
        return None
    if not any(re.search(hint, text, flags=re.IGNORECASE) for hint in _TRACKING_REQUEST_HINTS):
        return None

    for pattern in _TRACKING_ID_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).lstrip("#").strip()
    return None


def lookup_tracking_owner(tracking_id: str) -> str | None:
    """Resolve ownership via StockExit.user_uuid (JWT subject binding)."""
    try:
        from sqlmodel import Session, select

        from ...core.database import get_inventory_engine
        from ...models import StockExit
    except Exception:  # noqa: BLE001 — auth must fail closed without leaking internals
        return None

    normalized = tracking_id.strip()
    try:
        with Session(get_inventory_engine()) as session:
            row = session.exec(
                select(StockExit).where(StockExit.tracking_number == normalized)
            ).first()
            if row is None:
                # Also try without leading zeros / hash variants for numeric orders.
                alt = normalized.lstrip("0") or normalized
                if alt != normalized:
                    row = session.exec(
                        select(StockExit).where(StockExit.tracking_number == alt)
                    ).first()
            return str(row.user_uuid) if row is not None else None
    except Exception:  # noqa: BLE001
        return None


def authorize_tracking(
    *,
    question: str,
    user_uuid: str | None,
    owner_lookup: OwnerLookup | None = None,
) -> TrackingAuthResult:
    """Require session ownership when the user asks about a specific shipment."""
    tracking_id = extract_tracking_id(question)
    if not tracking_id:
        return TrackingAuthResult(authorized=True, tracking_id=None)

    if not user_uuid:
        return TrackingAuthResult(
            authorized=False,
            tracking_id=tracking_id,
            failure_type="content",
            guardrail="authorize_tracking",
            reason="missing_session",
        )

    lookup = owner_lookup or lookup_tracking_owner
    owner = lookup(tracking_id)

    # Same message whether missing or owned by someone else — authorization framing,
    # and avoid confirming whether the tracking exists.
    if owner is None or owner != user_uuid:
        return TrackingAuthResult(
            authorized=False,
            tracking_id=tracking_id,
            failure_type="content",
            guardrail="authorize_tracking",
            reason="unauthorized_tracking",
        )

    return TrackingAuthResult(authorized=True, tracking_id=tracking_id)
