"""Assemble FinalDocument from approved department sections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .constants import COUNTRY_CURRENCY, DEPARTMENT_CATALOG


def assemble_final_document(
    *,
    metadata: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build the consolidated pricing proposal.

    Only call when every active section is approved.
    """
    client = metadata.get("client_name") or "Cliente"
    country = metadata.get("client_country") or "US"
    currency = COUNTRY_CURRENCY.get(str(country), COUNTRY_CURRENCY.get(str(country).upper(), "USD"))
    generated_at = datetime.now(timezone.utc)

    lines = [
        f"# Propuesta comercial TrackFlow — {client}",
        "",
        f"- **País / moneda:** {country} / {currency}",
        f"- **Servicios:** {', '.join(metadata.get('services_requested') or []) or '—'}",
        f"- **Volumen:** {metadata.get('monthly_volume') or 'por confirmar'}",
        f"- **Deadline RFP:** {metadata.get('deadline') or '—'}",
        f"- **Generado:** {generated_at.isoformat()}",
        "",
        "---",
        "",
    ]

    section_ids: list[str] = []
    for section in sections:
        dept_id = section["department_id"]
        section_ids.append(dept_id)
        info = DEPARTMENT_CATALOG.get(dept_id, {})
        lines.append(f"## {info.get('name', dept_id)}")
        lines.append(f"_Aprobado por {section.get('approver')}_")
        lines.append("")
        lines.append(section.get("draft_content") or "_Sin contenido._")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(
        "_Documento generado automáticamente tras el sign-off de todos los departamentos activos._"
    )
    content = "\n".join(lines).strip() + "\n"
    return {
        "content": content,
        "currency": currency,
        "sections": section_ids,
        "generated_at": generated_at,
    }
