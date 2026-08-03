"""Department generator agents — one clearly separated generator per department."""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import COUNTRY_CURRENCY, DEPARTMENT_CATALOG


@dataclass(frozen=True)
class GeneratorResult:
    department_id: str
    draft_content: str
    method: str


def _currency_for(country: str | None) -> str:
    if not country:
        return "USD"
    return COUNTRY_CURRENCY.get(country, COUNTRY_CURRENCY.get(str(country).upper(), "USD"))


def _volume_discount_table(currency: str) -> str:
    return (
        "| Pedidos/mes | Descuento |\n"
        "| --- | --- |\n"
        f"| 1 – 2.000 | 0% sobre tarifa base ({currency}) |\n"
        f"| 2.001 – 5.000 | 5% |\n"
        f"| 5.001 – 10.000 | 8% |\n"
        f"| +10.000 | 12% |\n"
    )


def _feedback_block(feedback: list[str] | None) -> str:
    if not feedback:
        return ""
    lines = "\n".join(f"- {item}" for item in feedback)
    return f"\n## Correcciones aplicadas tras evaluación\n{lines}\n"


def generate_warehouse_section(
    *,
    metadata: dict,
    key_aspects: list[str],
    markdown: str = "",
    feedback: list[str] | None = None,
) -> GeneratorResult:
    """Warehouse Operations generator (Ana Whitfield)."""
    _ = markdown
    client = metadata.get("client_name") or "Cliente"
    country = metadata.get("client_country") or "US"
    currency = _currency_for(country)
    volume = metadata.get("monthly_volume") or 3000
    deadline = metadata.get("deadline") or "según RFP"
    aspects = "\n".join(f"- {a}" for a in key_aspects) or "- Capacidad y costo de almacenamiento"

    draft = f"""# Sección Warehouse Operations — {client}

## Alcance
Propuesta de almacenamiento, picking y packing para operación en **{country}**, cotizada en **{currency}**.

## Respuesta a aspectos clave
{aspects}

## Capacidad y onboarding
- Capacidad reservada para ~{volume} pedidos/mes con buffer del 20%.
- Tiempo de onboarding estimado: 10–15 días hábiles antes de {deadline}.
- Inventario en tiempo real vía integración estándar TrackFlow.

## Costos (costo final al cliente)
- Costo por pallet/mes: 18 {currency}
- Costo picking por pedido: 1.20 {currency}
- Sin revelar tarifas internas de proveedores; solo precios finales TrackFlow.

## SLA de entrega a tiempo
TrackFlow se compromete a un **SLA de entrega a tiempo del 97%** para pedidos despachados desde almacén (medido mensualmente).

## Descuentos por volumen
{_volume_discount_table(currency)}
{_feedback_block(feedback)}
"""
    return GeneratorResult(department_id="warehouse", draft_content=draft.strip() + "\n", method="template")


def generate_lastmile_section(
    *,
    metadata: dict,
    key_aspects: list[str],
    markdown: str = "",
    feedback: list[str] | None = None,
) -> GeneratorResult:
    """Last Mile and Carrier Management generator (Carlos Vega)."""
    _ = markdown
    client = metadata.get("client_name") or "Cliente"
    country = metadata.get("client_country") or "US"
    currency = _currency_for(country)
    volume = metadata.get("monthly_volume") or 3000
    aspects = "\n".join(f"- {a}" for a in key_aspects) or "- Red de carriers y SLA"

    draft = f"""# Sección Last Mile — {client}

## Alcance
Última milla para **{country}** con costo final al cliente en **{currency}**. No se publican tarifas negociadas con transportistas específicos.

## Respuesta a aspectos clave
{aspects}

## Red y cobertura
- Cobertura nacional en {country} mediante red certificada TrackFlow.
- Costo medio por envío (final): 4.50 {currency} (hasta 2 kg); zonas remotas con recargo publicado al cliente.
- Capacidad alineada a ~{volume} pedidos/mes.

## SLA de entrega a tiempo
TrackFlow se compromete a un **SLA de entrega a tiempo del 96%** en envíos de última milla.

## Descuentos por volumen
{_volume_discount_table(currency)}
{_feedback_block(feedback)}
"""
    return GeneratorResult(department_id="lastmile", draft_content=draft.strip() + "\n", method="template")


def generate_reverse_section(
    *,
    metadata: dict,
    key_aspects: list[str],
    markdown: str = "",
    feedback: list[str] | None = None,
) -> GeneratorResult:
    """Reverse Logistics generator (Sofía Ramos)."""
    _ = markdown
    client = metadata.get("client_name") or "Cliente"
    country = metadata.get("client_country") or "ES"
    currency = _currency_for(country)
    aspects = "\n".join(f"- {a}" for a in key_aspects) or "- Devoluciones e inspección"

    draft = f"""# Sección Reverse Logistics — {client}

## Alcance
Gestión de devoluciones e inspección para **{country}**, precios en **{currency}**.

## Respuesta a aspectos clave
{aspects}

## Tiempos y costos
- Tiempo de procesamiento de devoluciones: **48–72 horas** desde recepción en almacén (nunca menos de 48 horas).
- Costo por unidad procesada (final al cliente): 2.80 {currency}.
- Incluye inspección y reacondicionamiento básico.

## SLA de entrega a tiempo
Para reenvíos post-devolución, TrackFlow se compromete a un **SLA de entrega a tiempo del 95%**.

## Descuentos por volumen
{_volume_discount_table(currency)}
{_feedback_block(feedback)}
"""
    return GeneratorResult(department_id="reverse", draft_content=draft.strip() + "\n", method="template")


_GENERATORS = {
    "warehouse": generate_warehouse_section,
    "lastmile": generate_lastmile_section,
    "reverse": generate_reverse_section,
}


def generate_department_section(
    department_id: str,
    *,
    metadata: dict,
    key_aspects: list[str],
    markdown: str = "",
    feedback: list[str] | None = None,
) -> GeneratorResult:
    if department_id not in _GENERATORS:
        raise ValueError(f"Unknown department_id={department_id}")
    info = DEPARTMENT_CATALOG[department_id]
    _ = info
    return _GENERATORS[department_id](
        metadata=metadata,
        key_aspects=key_aspects,
        markdown=markdown,
        feedback=feedback,
    )
