from __future__ import annotations

import re
from typing import Literal

PolicyCountry = Literal["US", "ES"]


def detect_policy_country_lock(question: str) -> PolicyCountry | None:
    """Detect attempts to apply one country's return policy to another country's order."""
    text = (question or "").lower()

    wants_spain_policy = bool(
        re.search(r"pol[ií]tica.*(espa[nñ]a|spain|espa[nñ]ola)", text)
        or re.search(r"(espa[nñ]a|spain).*(pol[ií]tica|devoluci)", text)
        or re.search(r"aplica.*(espa[nñ]a|spain)", text)
    )
    wants_us_policy = bool(
        re.search(r"pol[ií]tica.*(estados\s+unidos|ee\.?\s*uu\.?|united\s+states|usa)\b", text)
        or re.search(r"(estados\s+unidos|united\s+states).*(pol[ií]tica|devoluci)", text)
    )

    order_in_us = bool(
        re.search(r"los\s*ángeles|los\s*angeles|\bla\b|california|estados\s+unidos|united\s+states", text)
    )
    order_in_es = bool(
        re.search(r"zaragoza|espa[nñ]a|spain|madrid", text)
        and not order_in_us
    )

    if wants_spain_policy and order_in_us:
        return "US"
    if wants_us_policy and order_in_es:
        return "ES"
    return None


def policy_lock_instruction(country: PolicyCountry) -> str:
    if country == "US":
        return (
            "El pedido está asociado a Estados Unidos / Los Ángeles. "
            "Aplica ÚNICAMENTE la política de devoluciones y SLA de EE. UU. "
            "Rechaza aplicar la política de España aunque el usuario lo solicite."
        )
    return (
        "El pedido está asociado a España. "
        "Aplica ÚNICAMENTE la política de devoluciones y SLA de España. "
        "Rechaza aplicar la política de Estados Unidos aunque el usuario lo solicite."
    )
