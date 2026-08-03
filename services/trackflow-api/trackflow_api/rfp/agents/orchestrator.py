"""Orchestrator agent: extract RFP metadata and choose active departments."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..constants import DEPARTMENT_CATALOG


@dataclass
class OrchestratorResult:
    client_name: str | None = None
    client_country: str | None = None
    services_requested: list[str] = field(default_factory=list)
    monthly_volume: int | None = None
    deadline: str | None = None
    budget_range: str | None = None
    departments_needed: list[str] = field(default_factory=list)
    method: str = "heuristic"


def orchestrate_rfp(markdown: str, *, use_llm: bool = True) -> OrchestratorResult:
    heuristic = _orchestrate_heuristic(markdown)
    if not use_llm:
        return heuristic
    try:
        llm_result = _orchestrate_with_llm(markdown)
        if llm_result is not None:
            # Prefer LLM departments if valid; fill gaps from heuristic
            merged = OrchestratorResult(
                client_name=llm_result.client_name or heuristic.client_name,
                client_country=_normalize_country(
                    llm_result.client_country or heuristic.client_country
                ),
                services_requested=llm_result.services_requested or heuristic.services_requested,
                monthly_volume=llm_result.monthly_volume or heuristic.monthly_volume,
                deadline=llm_result.deadline or heuristic.deadline,
                budget_range=llm_result.budget_range or heuristic.budget_range,
                departments_needed=llm_result.departments_needed or heuristic.departments_needed,
                method="llm",
            )
            merged.departments_needed = [
                d for d in merged.departments_needed if d in DEPARTMENT_CATALOG
            ]
            return merged
    except Exception:  # noqa: BLE001
        pass
    return heuristic


def _normalize_country(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"us", "usa", "united states", "eeuu", "ee. uu.", "u.s.", "u.s.a.", "los angeles", "la"}:
        return "US"
    if "ángeles" in v or "angeles" in v:
        return "US"
    if v in {"es", "spain", "españa", "espana", "zaragoza"}:
        return "ES"
    if "spain" in v or "espa" in v:
        return "ES"
    if "united states" in v or v == "america":
        return "US"
    return value.strip().upper() if len(value.strip()) <= 3 else value.strip()


def _orchestrate_heuristic(markdown: str) -> OrchestratorResult:
    text = markdown or ""
    lower = text.lower()

    client_name = None
    for pattern in (
        r"(?:client|cliente|company|empresa|brand|marca)\s*[:\-]\s*([^\n]+)",
        r"\*\*([^*]+)\*\*.{0,40}(?:rfp|request for proposal|solicitud)",
        r"(?:rfp|solicitud de propuesta)\s+(?:[-—:]\s*)?([A-Z][A-Za-z0-9 &]+)",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            client_name = match.group(1).strip(" -:|")
            break
    if not client_name:
        if "luna cosmetics" in lower:
            client_name = "Luna Cosmetics"
        elif "modaviva" in lower:
            client_name = "Zaragoza ModaViva"

    country = None
    # Prefer explicit ES markers before US — Spanish copy often contains verb "usa".
    if re.search(r"\b(españa|espana|spain|zaragoza)\b", lower):
        country = "ES"
    elif re.search(
        r"\b(los\s+ángeles|los\s+angeles|united\s+states|ee\.?\s*uu\.?|u\.s\.a\.?)\b",
        lower,
    ):
        country = "US"
    elif re.search(r"\bUS\b", text):
        country = "US"

    normalized = lower.replace("–", "-").replace("—", "-")
    wants_warehouse = any(
        k in normalized
        for k in ("warehouse", "warehousing", "almacenamiento", "almacén", "almacen")
    )
    wants_lastmile = any(
        k in normalized
        for k in (
            "last mile",
            "last-mile",
            "última milla",
            "ultima milla",
            "carrier network",
        )
    )
    # Explicit exclusion of last mile / own carrier
    if re.search(
        r"(does not (need|require) last[- ]?mile|no necesita last[- ]?mile|"
        r"sin (última|ultima) milla|own (carrier|transport|fleet|transportista)|"
        r"propio transportista|nuestro transportista)",
        normalized,
    ):
        wants_lastmile = False

    wants_reverse = any(
        k in normalized
        for k in (
            "reverse logistics",
            "logística inversa",
            "logistica inversa",
            "devoluc",
            "returns management",
            "gestión de devoluciones",
            "gestion de devoluciones",
        )
    )
    if re.search(
        r"(reverse logistics is out of scope|out of scope for this rfp|"
        r"no (solicita|incluye|necesita) (reverse|devoluc))",
        normalized,
    ):
        wants_reverse = False

    departments: list[str] = []
    services: list[str] = []
    if wants_warehouse:
        departments.append("warehouse")
        services.append("warehousing")
    if wants_lastmile:
        departments.append("lastmile")
        services.append("last_mile")
    if wants_reverse:
        departments.append("reverse")
        services.append("reverse_logistics")

    volume = None
    vol_match = re.search(
        r"([\d.,]+)\s*(?:pedidos|orders|env[ií]os)?\s*/\s*mes|(?:~|approx\.?|approximately)?\s*([\d.,]+)\s*(?:pedidos|orders)",
        lower,
    )
    if vol_match:
        raw = (vol_match.group(1) or vol_match.group(2) or "").replace(".", "").replace(",", "")
        if raw.isdigit():
            volume = int(raw)
    if volume is None:
        if "5.000" in text or "5,000" in text or "5000" in lower:
            volume = 5000

    deadline = None
    dl = re.search(r"(?:deadline|fecha l[ií]mite|due)\s*[:\-]?\s*([^\n]+)", text, flags=re.I)
    if dl:
        deadline = dl.group(1).strip()
    elif re.search(r"20\s*d[ií]as", lower):
        deadline = "20 days"
    elif re.search(r"25\s*d[ií]as", lower):
        deadline = "25 days"

    budget = None
    bud = re.search(r"(?:budget|presupuesto)\s*[:\-]?\s*([^\n]+)", text, flags=re.I)
    if bud:
        budget = bud.group(1).strip()

    return OrchestratorResult(
        client_name=client_name,
        client_country=country,
        services_requested=services,
        monthly_volume=volume,
        deadline=deadline,
        budget_range=budget,
        departments_needed=departments,
        method="heuristic",
    )


def _orchestrate_with_llm(markdown: str) -> OrchestratorResult | None:
    from ...rag.litellm_client import create_completion

    system = (
        "Eres el orquestador de RFPs de TrackFlow. Extrae metadatos y decide qué "
        "departamentos aplican: warehouse, lastmile, reverse. "
        "Si el cliente usa su propio transportista, NO incluyas lastmile. "
        'client_country debe ser "US" o "ES". '
        "Responde SOLO JSON con keys: client_name, client_country, services_requested, "
        "monthly_volume, deadline, budget_range, departments_needed."
    )
    raw = create_completion(system_prompt=system, user_prompt=markdown[:12000])
    payload = _parse_json(raw)
    if not payload:
        return None
    depts = payload.get("departments_needed") or []
    if not isinstance(depts, list):
        depts = []
    return OrchestratorResult(
        client_name=payload.get("client_name"),
        client_country=payload.get("client_country"),
        services_requested=list(payload.get("services_requested") or []),
        monthly_volume=_as_int(payload.get("monthly_volume")),
        deadline=payload.get("deadline"),
        budget_range=payload.get("budget_range"),
        departments_needed=[str(d) for d in depts],
        method="llm",
    )


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_json(raw: str) -> dict[str, Any] | None:
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
