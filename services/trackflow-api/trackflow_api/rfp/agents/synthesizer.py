"""Synthesizer: deterministic merge of worker outputs into a Sales-facing brief."""

from __future__ import annotations

from ..constants import COUNTRY_CURRENCY, DEPARTMENT_CATALOG
from .workers import WorkerResult


def synthesize_sales_brief(
    *,
    metadata: dict,
    workers: list[WorkerResult],
    readability: dict | None = None,
    cost_estimate: dict | None = None,
) -> str:
    """Build a Markdown brief Sales can use without reading the original RFP."""
    client = metadata.get("client_name") or "Cliente sin nombre"
    country = metadata.get("client_country") or "—"
    currency = COUNTRY_CURRENCY.get(str(country), COUNTRY_CURRENCY.get(str(country).upper(), "—"))
    services = ", ".join(metadata.get("services_requested") or []) or "—"
    volume = metadata.get("monthly_volume")
    volume_txt = f"{volume} pedidos/mes" if volume else "por confirmar"
    deadline = metadata.get("deadline") or "por confirmar"
    budget = metadata.get("budget_range") or "no indicado"

    lines = [
        f"# Brief de intake — {client}",
        "",
        "## Metadatos",
        f"- **Cliente:** {client}",
        f"- **País / moneda:** {country} / {currency}",
        f"- **Servicios:** {services}",
        f"- **Volumen:** {volume_txt}",
        f"- **Deadline:** {deadline}",
        f"- **Presupuesto ref.:** {budget}",
    ]

    if cost_estimate:
        lines.extend(
            [
                "",
                "## Estimación de esfuerzo de procesamiento",
                f"- **Banda:** {cost_estimate.get('band')} (score {cost_estimate.get('score_1_to_5')}/5)",
                f"- **Tokens estimados:** {cost_estimate.get('estimated_input_tokens')}",
                f"- **Minutos estimados:** {cost_estimate.get('estimated_minutes')}",
            ]
        )
    if readability:
        lines.extend(
            [
                "",
                "## Métricas de legibilidad del documento",
                f"- Words: {readability.get('word_count')}",
                f"- Flesch Reading Ease: {readability.get('flesch_reading_ease')}",
                f"- Flesch-Kincaid Grade: {readability.get('flesch_kincaid_grade')}",
                f"- Gunning Fog: {readability.get('gunning_fog')}",
            ]
        )

    lines.extend(["", "## Qué pedir a cada departamento", ""])
    if not workers:
        lines.append("_No se identificaron departamentos activos._")
    for worker in workers:
        info = DEPARTMENT_CATALOG.get(worker.department_id, {})
        name = info.get("name", worker.department_id)
        lines.append(f"### {name} (`{worker.department_id}`)")
        lines.append(f"- **Dirigirse a:** {worker.approver}")
        for aspect in worker.key_aspects:
            lines.append(f"- {aspect}")
        lines.append("")

    lines.append(
        "_Parte 1 completa: confirma el routing para pasar a generación de borrador (Parte 2)._"
    )
    return "\n".join(lines).strip() + "\n"
