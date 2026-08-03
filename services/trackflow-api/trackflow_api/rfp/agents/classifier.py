"""Classifier agent: decide whether a document is a TrackFlow logistics RFP."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClassifierResult:
    is_rfp: bool
    confidence: float
    reason: str
    method: str


_RFP_HINTS = (
    "request for proposal",
    "rfp",
    "solicitud de propuesta",
    "propuesta comercial",
    "pricing proposal",
    "cotización",
    "cotizacion",
    "warehous",
    "almacenamiento",
    "última milla",
    "ultima milla",
    "last mile",
    "reverse logistics",
    "devoluciones",
    "pedidos/mes",
    "orders/month",
)

_NON_RFP_HINTS = (
    "we are pleased to offer",
    "our carrier rates",
    "tarifa de envío",
    "tarifas de envio",
    "supplier offer",
    "oferta de transportista",
    "new shipping rates for trackflow",
    "as your carrier partner",
)


def classify_document(markdown: str, *, use_llm: bool = True) -> ClassifierResult:
    """
    Classify whether the markdown is a client RFP for TrackFlow logistics.

    Uses deterministic heuristics first (stable for tests/fixtures). Optionally
    refines with LiteLLM when available.
    """
    heuristic = _classify_heuristic(markdown)
    if not use_llm:
        return heuristic

    try:
        llm_result = _classify_with_llm(markdown)
        if llm_result is not None:
            return llm_result
    except Exception:  # noqa: BLE001
        pass
    return heuristic


def _classify_heuristic(markdown: str) -> ClassifierResult:
    text = (markdown or "").lower()
    non_hits = sum(1 for hint in _NON_RFP_HINTS if hint in text)
    if non_hits >= 1 and "request for proposal" not in text and "solicitud de propuesta" not in text:
        return ClassifierResult(
            is_rfp=False,
            confidence=0.92,
            reason=(
                "El documento parece una oferta entrante de proveedor/transportista, "
                "no una RFP de un cliente."
            ),
            method="heuristic",
        )

    rfp_hits = sum(1 for hint in _RFP_HINTS if hint in text)
    has_client_ask = bool(
        re.search(r"\b(solicit|request|necesit|looking for|require)\w*\b", text)
    )
    logistics_scope = any(
        k in text
        for k in (
            "warehouse",
            "almacen",
            "last mile",
            "última milla",
            "ultima milla",
            "reverse",
            "devoluc",
        )
    )

    if rfp_hits >= 2 and logistics_scope and has_client_ask:
        return ClassifierResult(
            is_rfp=True,
            confidence=0.9,
            reason="Documento con señales de RFP logística de cliente (servicios + solicitud).",
            method="heuristic",
        )
    if logistics_scope and ("rfp" in text or "proposal" in text or "propuesta" in text):
        return ClassifierResult(
            is_rfp=True,
            confidence=0.75,
            reason="Documento etiquetado como propuesta/RFP con alcance logístico.",
            method="heuristic",
        )

    return ClassifierResult(
        is_rfp=False,
        confidence=0.7,
        reason="No se detectaron señales suficientes de una RFP logística de cliente TrackFlow.",
        method="heuristic",
    )


def _classify_with_llm(markdown: str) -> ClassifierResult | None:
    from ...rag.litellm_client import create_completion

    system = (
        "Eres el clasificador de intake de TrackFlow. Decide si el documento es una RFP "
        "de un cliente de e-commerce que pide propuesta de warehousing, last mile y/o "
        "reverse logistics en EE.UU. o España. "
        "NO es RFP si es oferta de un proveedor/transportista hacia TrackFlow. "
        'Responde SOLO JSON: {"is_rfp": bool, "confidence": float, "reason": string}'
    )
    user = f"Documento (Markdown):\n\n{markdown[:12000]}"
    raw = create_completion(system_prompt=system, user_prompt=user)
    payload = _parse_json_object(raw)
    if payload is None or "is_rfp" not in payload:
        return None
    return ClassifierResult(
        is_rfp=bool(payload["is_rfp"]),
        confidence=float(payload.get("confidence") or 0.5),
        reason=str(payload.get("reason") or "Clasificación LLM"),
        method="llm",
    )


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
