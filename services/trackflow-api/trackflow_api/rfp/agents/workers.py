"""Department worker agents: extract key aspects and who to ask."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from ..constants import DEPARTMENT_CATALOG


@dataclass
class WorkerResult:
    department_id: str
    approver: str
    key_aspects: list[str] = field(default_factory=list)
    method: str = "heuristic"


def run_department_worker(
    department_id: str,
    *,
    markdown: str,
    metadata: dict,
) -> WorkerResult:
    """Analyze what a single department must contribute for this RFP."""
    info = DEPARTMENT_CATALOG[department_id]
    lower = (markdown or "").lower()
    client = metadata.get("client_name") or "el cliente"
    country = metadata.get("client_country") or "mercado indicado"
    volume = metadata.get("monthly_volume")
    volume_txt = f"~{volume} pedidos/mes" if volume else "volumen por confirmar"
    deadline = metadata.get("deadline") or "fecha límite por confirmar"
    currency = "USD" if country == "US" else "EUR" if country == "ES" else "moneda según país"

    aspects: list[str] = []
    if department_id == "warehouse":
        aspects = [
            f"Confirmar capacidad de almacenamiento y slotting para {client} ({volume_txt}).",
            f"Cotizar costo por pallet/SKU en {currency} para operación en {country}.",
            f"Estimar tiempo de onboarding del almacén antes de {deadline}.",
            "Definir requisitos de inventario en tiempo real / integraciones.",
        ]
        if "cosmetic" in lower or "cosmética" in lower or "cosmetica" in lower:
            aspects.append("Revisar handling de cosmética (lote, caducidad, temperatura si aplica).")
        if "moda" in lower or "fashion" in lower:
            aspects.append("Validar picking de moda (tallas, SKUs altos, estacionalidad).")
    elif department_id == "lastmile":
        aspects = [
            f"Diseñar red de carriers y costo por envío en {currency} para {country}.",
            f"Comprometer SLA de entrega a tiempo (%) alineado a {volume_txt}.",
            "Confirmar cobertura geográfica solicitada y excepciones (islas/zonales).",
            "Preparar costo final al cliente sin revelar tarifas negociadas con carriers.",
        ]
    elif department_id == "reverse":
        aspects = [
            f"Cotizar costo y lead time de devoluciones para {client} (mínimo 48h de procesamiento).",
            "Definir flujo de inspección/reacondicionamiento e integración con la tienda.",
            f"Alinear moneda {currency} y descuentos por volumen de returns si aplica.",
            f"Confirmar capacidad operativa antes de {deadline}.",
        ]
    else:
        aspects = [f"Revisar alcance de {info['name']} según la RFP."]

    return WorkerResult(
        department_id=department_id,
        approver=info["approver"],
        key_aspects=aspects,
        method="heuristic",
    )


def run_workers_parallel(
    department_ids: list[str],
    *,
    markdown: str,
    metadata: dict,
) -> list[WorkerResult]:
    """Fan-out department workers in parallel; preserve catalog order in output."""
    if not department_ids:
        return []

    results_by_id: dict[str, WorkerResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(department_ids))) as pool:
        futures = {
            pool.submit(
                run_department_worker,
                dept_id,
                markdown=markdown,
                metadata=metadata,
            ): dept_id
            for dept_id in department_ids
        }
        for future in as_completed(futures):
            result = future.result()
            results_by_id[result.department_id] = result

    return [results_by_id[d] for d in department_ids if d in results_by_id]
