"""Sensitive-content filter for memory proposals (TrackFlow CONTEXT)."""

from __future__ import annotations

import re

_FORBIDDEN_PATTERNS = (
    # Exact B2C / B2B location data and warehouse routes
    r"\bdirecci[oó]n\s+(exacta|completa|del\s+cliente|de\s+entrega)\b",
    r"\bcalle\s+\w+.*(n[uú]mero|\d{1,4})\b",
    r"\brutas?\s+internas?\b",
    r"\bubicaci[oó]n\s+exacta\b",
    r"\balmac[eé]n.*(coordenadas|direcci[oó]n\s+exacta)\b",
    r"\b(latitud|longitud|gps)\b",
    # One-off package / tracking dumps
    r"\btracking\s+[A-Z0-9_-]{6,}\b.*\b(solo|puntual|esta\s+vez)\b",
    # Active commercial negotiations
    r"\b(negociaci[oó]n|contrato\s+en\s+curso|oferta\s+comercial\s+activa)\b",
    r"\btarifa(s)?\s+negociad",
)


def contains_forbidden_memory_content(text: str) -> bool:
    lowered = (text or "").lower()
    return any(re.search(pattern, lowered) for pattern in _FORBIDDEN_PATTERNS)
