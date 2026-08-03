"""Structured evaluators for generated RFP sections (Parte 2)."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from ..constants import COUNTRY_CURRENCY
from ..ingest import compute_readability_metrics


@dataclass
class EvaluatorResult:
    name: str
    passed: bool
    score: float | None = None
    reasons: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "score": self.score,
            "reasons": list(self.reasons),
            "details": dict(self.details),
        }


@dataclass
class EvaluationBundle:
    readability: EvaluatorResult
    pertinence: EvaluatorResult
    compliance: EvaluatorResult

    @property
    def passed(self) -> bool:
        return (
            self.readability.passed
            and self.pertinence.passed
            and self.compliance.passed
        )

    def feedback_for_generator(self) -> list[str]:
        items: list[str] = []
        for result in (self.readability, self.pertinence, self.compliance):
            if not result.passed:
                for reason in result.reasons:
                    items.append(f"[{result.name}] {reason}")
        return items

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_passed": self.passed,
            "readability": self.readability.to_dict(),
            "pertinence": self.pertinence.to_dict(),
            "compliance": self.compliance.to_dict(),
        }


# Minimum readable length / soft grade ceiling for proposal drafts.
_MIN_WORDS = 40
_MAX_FK_GRADE = 18.0


def evaluate_readability(draft: str) -> EvaluatorResult:
    metrics = compute_readability_metrics(draft)
    reasons: list[str] = []
    words = int(metrics.get("word_count") or 0)
    if words < _MIN_WORDS:
        reasons.append(f"Borrador demasiado corto ({words} palabras; mínimo {_MIN_WORDS}).")
    grade = metrics.get("flesch_kincaid_grade")
    if isinstance(grade, (int, float)) and float(grade) > _MAX_FK_GRADE:
        reasons.append(
            f"Flesch-Kincaid grade {grade} supera el umbral {_MAX_FK_GRADE} (simplificar redacción)."
        )
    passed = len(reasons) == 0
    if passed:
        reasons.append("Legibilidad dentro de umbrales operativos.")
    return EvaluatorResult(
        name="readability",
        passed=passed,
        score=float(grade) if isinstance(grade, (int, float)) else None,
        reasons=reasons,
        details=metrics,
    )


def evaluate_pertinence(
    draft: str,
    *,
    metadata: dict,
    key_aspects: list[str],
    department_id: str,
) -> EvaluatorResult:
    lower = (draft or "").lower()
    reasons: list[str] = []
    client = (metadata.get("client_name") or "").lower()
    if client and client not in lower:
        reasons.append(f"El borrador no menciona al cliente '{metadata.get('client_name')}'.")

    dept_signals = {
        "warehouse": ("almacen", "warehouse", "pallet", "picking", "onboarding"),
        "lastmile": ("última milla", "ultima milla", "last mile", "envío", "envio", "sla"),
        "reverse": ("devoluc", "reverse", "48", "reacondicion"),
    }
    signals = dept_signals.get(department_id, ())
    if signals and not any(s in lower for s in signals):
        reasons.append(f"Falta contenido propio del departamento `{department_id}`.")

    aspect_hits = 0
    for aspect in key_aspects[:4]:
        tokens = [t for t in re.findall(r"[a-záéíóúñ]{5,}", aspect.lower()) if t not in {"para", "según", "desde"}]
        if any(tok in lower for tok in tokens[:3]):
            aspect_hits += 1
    if key_aspects and aspect_hits == 0:
        reasons.append("El borrador no refleja los key_aspects de la Parte 1.")

    # RFP service scope
    services = metadata.get("services_requested") or []
    if department_id == "warehouse" and services and "warehousing" in services:
        if not any(k in lower for k in ("almacen", "warehouse", "pallet")):
            reasons.append("No responde el servicio de warehousing solicitado.")
    if department_id == "lastmile" and "last_mile" in services:
        if not any(k in lower for k in ("envío", "envio", "last mile", "milla")):
            reasons.append("No responde el servicio de last mile solicitado.")
    if department_id == "reverse" and "reverse_logistics" in services:
        if not any(k in lower for k in ("devoluc", "reverse")):
            reasons.append("No responde el servicio de reverse logistics solicitado.")

    passed = len(reasons) == 0
    if passed:
        reasons.append("El borrador es pertinente respecto a la RFP y los aspectos clave.")
    score = 1.0 if passed else max(0.0, 1.0 - 0.25 * len(reasons))
    return EvaluatorResult(
        name="pertinence",
        passed=passed,
        score=round(score, 2),
        reasons=reasons,
        details={"aspect_hits": aspect_hits, "department_id": department_id},
    )


def evaluate_compliance(draft: str, *, metadata: dict, department_id: str) -> EvaluatorResult:
    """Verify CONTEXT §5 business rules with structured checks (not free-form opinion)."""
    text = draft or ""
    lower = text.lower()
    country = metadata.get("client_country") or "US"
    expected_currency = COUNTRY_CURRENCY.get(str(country), COUNTRY_CURRENCY.get(str(country).upper(), "USD"))
    checks: list[dict[str, Any]] = []
    reasons: list[str] = []

    # 1) Currency
    has_currency = expected_currency.lower() in lower or expected_currency in text
    wrong_other = (expected_currency == "USD" and " eur" in f" {lower}") or (
        expected_currency == "EUR" and re.search(r"\busd\b", lower)
    )
    currency_ok = has_currency and not wrong_other
    checks.append(
        {
            "rule": "currency_matches_client_country",
            "expected": expected_currency,
            "passed": currency_ok,
        }
    )
    if not currency_ok:
        reasons.append(
            f"La moneda debe ser {expected_currency} según client_country={country}."
        )

    # 2) On-time SLA %
    sla_match = re.search(r"sla[^\n%]{0,40}?(\d{2,3})\s*%", lower) or re.search(
        r"(\d{2,3})\s*%[^\n]{0,40}sla|entrega a tiempo[^\n%]{0,40}(\d{2,3})\s*%",
        lower,
    )
    sla_ok = sla_match is not None
    checks.append({"rule": "on_time_sla_percent_present", "passed": sla_ok})
    if not sla_ok:
        reasons.append("Debe indicar el SLA de entrega a tiempo en porcentaje (%).")

    # 3) Reverse processing >= 48h (always enforce if reverse section; also if draft promises faster)
    too_fast = re.search(
        r"(?<!nunca\s)(?<!no\s)(menos de\s*48|under\s*48|24\s*horas|same[- ]day returns|en\s*24\s*horas)",
        lower,
    )
    has_48 = re.search(
        r"(48\s*[\-–]\s*72\s*horas|48\s*horas|m[ií]nimo\s*48|nunca menos de 48|no menos de 48)",
        lower,
    )
    if department_id == "reverse":
        reverse_ok = has_48 is not None and too_fast is None
        checks.append({"rule": "reverse_processing_min_48h", "passed": reverse_ok})
        if not reverse_ok:
            reasons.append(
                "Reverse Logistics no puede prometer procesamiento de devoluciones en menos de 48 horas."
            )
    else:
        reverse_ok = too_fast is None
        checks.append({"rule": "no_sub_48h_return_promise", "passed": reverse_ok})
        if not reverse_ok:
            reasons.append("No se puede prometer devoluciones en menos de 48 horas.")

    # 4) Volume discount table
    has_discount_table = (
        "descuento" in lower
        and "|" in text
        and bool(re.search(r"\d+\s*%", text))
    )
    checks.append({"rule": "volume_discount_table_present", "passed": has_discount_table})
    if not has_discount_table:
        reasons.append("Debe incluir una tabla de descuentos por volumen.")

    # 5) No negotiated carrier tariffs disclosure
    leaked = re.search(
        r"(tarifa negociada|tarifas negociadas|rate card (con|de) (dhl|seur|mrw|fedex)|costo carrier interno)",
        lower,
    )
    leak_ok = leaked is None
    checks.append({"rule": "no_negotiated_carrier_rates", "passed": leak_ok})
    if not leak_ok:
        reasons.append(
            "No revelar tarifas negociadas con transportistas; solo costo final al cliente."
        )

    passed = all(c["passed"] for c in checks)
    if passed:
        reasons.append("Cumple los lineamientos §5 del CONTEXT de TrackFlow.")
    score = round(sum(1 for c in checks if c["passed"]) / max(len(checks), 1), 2)
    return EvaluatorResult(
        name="compliance",
        passed=passed,
        score=score,
        reasons=reasons,
        details={"checks": checks, "expected_currency": expected_currency},
    )


def run_evaluators_parallel(
    draft: str,
    *,
    metadata: dict,
    key_aspects: list[str],
    department_id: str,
) -> EvaluationBundle:
    """Run readability, pertinence and compliance evaluators in parallel."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_read = pool.submit(evaluate_readability, draft)
        fut_pert = pool.submit(
            evaluate_pertinence,
            draft,
            metadata=metadata,
            key_aspects=key_aspects,
            department_id=department_id,
        )
        fut_comp = pool.submit(
            evaluate_compliance,
            draft,
            metadata=metadata,
            department_id=department_id,
        )
        futures = {fut_read: "readability", fut_pert: "pertinence", fut_comp: "compliance"}
        results: dict[str, EvaluatorResult] = {}
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()

    return EvaluationBundle(
        readability=results["readability"],
        pertinence=results["pertinence"],
        compliance=results["compliance"],
    )
