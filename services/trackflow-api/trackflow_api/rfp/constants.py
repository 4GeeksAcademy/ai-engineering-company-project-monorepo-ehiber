"""TrackFlow RFP department catalog and ticket statuses (Hito 9 context)."""

from __future__ import annotations

from typing import TypedDict


class DepartmentInfo(TypedDict):
    department_id: str
    name: str
    approver: str
    contributes: str


DEPARTMENT_CATALOG: dict[str, DepartmentInfo] = {
    "warehouse": {
        "department_id": "warehouse",
        "name": "Warehouse Operations",
        "approver": "Ana Whitfield",
        "contributes": (
            "Capacidad de almacenamiento, costo por pallet/SKU, tiempo de onboarding"
        ),
    },
    "lastmile": {
        "department_id": "lastmile",
        "name": "Last Mile and Carrier Management",
        "approver": "Carlos Vega",
        "contributes": (
            "Costo por envío, transportistas disponibles según destino, SLA de entrega"
        ),
    },
    "reverse": {
        "department_id": "reverse",
        "name": "Reverse Logistics",
        "approver": "Sofía Ramos",
        "contributes": (
            "Costo y tiempo de procesamiento de devoluciones (si el cliente lo solicita)"
        ),
    },
}

RFP_STATUSES = (
    "analizando",
    "esperando_aprobación",
    "generando_borrador",
    "en_evaluación",
    "terminado",
    "descartado",
)

COUNTRY_CURRENCY = {
    "US": "USD",
    "USA": "USD",
    "United States": "USD",
    "EE. UU.": "USD",
    "EEUU": "USD",
    "ES": "EUR",
    "Spain": "EUR",
    "España": "EUR",
}

MAX_GENERATOR_ITERATIONS = 2
