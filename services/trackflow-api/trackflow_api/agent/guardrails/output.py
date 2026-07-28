from __future__ import annotations

import re

from .types import OutputGuardResult

_SENSITIVE_PATTERNS = (
    r"tarifa(s)?\s+negociad",
    r"negotiated\s+rate",
    r"coordenadas",
    r"latitud|longitud",
    r"ubicaci[oó]n\s+exacta",
    r"ruta\s+interna",
    r"internal\s+route",
    r"direcci[oó]n\s+del\s+almac[eé]n",
    r"warehouse\s+address",
)

_SYSTEM_LEAK_PATTERNS = (
    r"system\s+prompt",
    r"mis\s+instrucciones\s+(internas|del\s+sistema)",
    r"<<<CONTEXTO_RECUPERADO",
    r"<<<DATOS_TOOL",
)


def validate_output(answer: str) -> OutputGuardResult:
    text = (answer or "").strip()
    if not text:
        return OutputGuardResult(
            ok=False,
            answer=(
                "No pude generar una respuesta válida. "
                "Reformula tu consulta de soporte logístico de TrackFlow."
            ),
            failure_type="structural",
            guardrail="validate_output",
            reason="empty_answer",
        )

    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in _SENSITIVE_PATTERNS):
        return OutputGuardResult(
            ok=False,
            answer=(
                "No puedo compartir tarifas negociadas, ubicaciones exactas de almacén "
                "ni rutas internas. Si necesitas soporte de envíos, devoluciones o "
                "incidencias, indícame el dato de tu pedido autenticado."
            ),
            failure_type="content",
            guardrail="validate_output",
            reason="sensitive_data",
        )

    if any(re.search(pattern, lowered) for pattern in _SYSTEM_LEAK_PATTERNS):
        return OutputGuardResult(
            ok=False,
            answer=(
                "No puedo exponer instrucciones internas. "
                "Puedo ayudarte con tracking, devoluciones o incidencias de TrackFlow."
            ),
            failure_type="security",
            guardrail="validate_output",
            reason="system_leak",
        )

    return OutputGuardResult(ok=True, answer=text)
