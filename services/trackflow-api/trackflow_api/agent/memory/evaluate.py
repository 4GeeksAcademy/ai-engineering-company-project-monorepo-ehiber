"""Heuristic self-evaluation: what is worth proposing to CX memory."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .sensitive import contains_forbidden_memory_content

_CARRIERS = (
    "seur",
    "mrw",
    "dhl",
    "fedex",
    "ups",
    "estafeta",
    "carrier local",
    "transportista",
)

_MEMORABLE_PATTERNS = (
    r"\b(ya\s+no\s+cubre|dej[oó]\s+de\s+operar|hay\s+que\s+usar|desde\s+el\s+mes\s+pasado)\b",
    r"\b(huelga|retrasos?\s+reportados|van\s+tres\s+tickets|recurrente)\b",
    r"\b(siempre\s+quiere|reporte\s+mensual|desglose\s+de\s+devoluciones|preferencia)\b",
    r"\b(no\s+por\s+un\s+problema\s+(nuestro|de\s+trackflow))\b",
)

_NOT_MEMORABLE_PATTERNS = (
    r"\b(tracking|pedido|paquete)\s*[#:.-]?\s*[A-Za-z0-9_-]+\b",
    r"\b(d[oó]nde\s+est[aá]|estado\s+del\s+pedido)\b",
    r"\b(ya\s+qued[oó]\s+resuelto|perfecto,?\s+ya\s+qued[oó]|gracias)\b",
    r"\b(trad[uú]ce(me)?|translate)\b",
    r"\b(ensayo|tarea|c[oó]digo)\b",
)


@dataclass(frozen=True)
class MemoryCandidate:
    should_propose: bool
    content: str
    carrier: str | None
    country: str | None
    topic: str
    consolidation_key: str
    reason: str


def evaluate_memory_candidate(*, question: str, answer: str) -> MemoryCandidate | None:
    """Decide whether the turn contains a durable CX correction/pattern."""
    combined = f"{question}\n{answer}".strip()
    lowered = combined.lower()

    if contains_forbidden_memory_content(combined):
        return None

    if any(re.search(pattern, lowered) for pattern in _NOT_MEMORABLE_PATTERNS):
        # Tracking/one-off/close/translate — never propose.
        if not any(re.search(pattern, lowered) for pattern in _MEMORABLE_PATTERNS):
            return None
        # If both match, prefer not memorable for pure tracking questions.
        if re.search(r"\b(d[oó]nde\s+est[aá]|tracking\s+[A-Za-z0-9_-]+)\b", lowered):
            return None

    if not any(re.search(pattern, lowered) for pattern in _MEMORABLE_PATTERNS):
        return None

    carrier = _detect_carrier(lowered)
    country = _detect_country(lowered)
    topic = _detect_topic(lowered)
    content = _summarize_candidate(question=question, answer=answer, topic=topic)
    if contains_forbidden_memory_content(content):
        return None

    key = f"{(carrier or 'general').lower()}|{(country or 'ALL').upper()}|{topic}"
    return MemoryCandidate(
        should_propose=True,
        content=content,
        carrier=carrier,
        country=country,
        topic=topic,
        consolidation_key=key,
        reason="memorable_cx_pattern",
    )


def _detect_carrier(text: str) -> str | None:
    for name in _CARRIERS:
        if name in text:
            return name.upper() if name != "carrier local" else "LOCAL"
    return None


def _detect_country(text: str) -> str | None:
    if re.search(r"zaragoza|espa[nñ]a|catalu[nñ]a|spain|\bzgz\b", text):
        return "ES"
    if re.search(r"los\s*angeles|los\s*ángeles|\bla\b|estados\s+unidos|portuaria|united\s+states", text):
        return "US"
    return None


def _detect_topic(text: str) -> str:
    if re.search(r"reporte|preferencia|devoluciones\s+primero|mensual", text):
        return "b2b_report_preference"
    if re.search(r"huelga|retraso|tickets|incidencia", text):
        return "recurring_incident_context"
    if re.search(r"cubre|cobertura|carrier|transportista|ruta|zona", text):
        return "carrier_assignment_rule"
    return "cx_operational_note"


def _summarize_candidate(*, question: str, answer: str, topic: str) -> str:
    # Prefer the user correction when present; otherwise keep a short answer slice.
    source = question.strip() if len(question.strip()) >= 20 else answer.strip()
    cleaned = re.sub(r"\s+", " ", source).strip()
    if len(cleaned) > 280:
        cleaned = cleaned[:277] + "..."
    return f"[{topic}] {cleaned}"
