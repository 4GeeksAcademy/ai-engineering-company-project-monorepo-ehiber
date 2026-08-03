"""Unit tests for RFP classifier and department workers (Hito 9 Parte 1)."""

from __future__ import annotations

from pathlib import Path

from trackflow_api.core.config import REPO_ROOT
from trackflow_api.rfp.agents.classifier import classify_document
from trackflow_api.rfp.agents.orchestrator import orchestrate_rfp
from trackflow_api.rfp.agents.workers import run_department_worker
from trackflow_api.rfp.graph import run_rfp_part1
from trackflow_api.rfp.ingest import (
    build_simple_pdf,
    compute_readability_metrics,
    estimate_processing_cost,
    pdf_bytes_to_markdown,
)

FIXTURES = REPO_ROOT / "docs" / "agentic-workflow" / "fixtures" / "rfp"


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_classifier_accepts_luna_rfp():
    result = classify_document(_read_fixture("luna-cosmetics.md"), use_llm=False)
    assert result.is_rfp is True
    assert result.confidence >= 0.7


def test_classifier_accepts_modaviva_rfp():
    result = classify_document(_read_fixture("modaviva.md"), use_llm=False)
    assert result.is_rfp is True


def test_classifier_rejects_carrier_offer():
    result = classify_document(_read_fixture("carrier-offer.md"), use_llm=False)
    assert result.is_rfp is False
    assert "proveedor" in result.reason.lower() or "oferta" in result.reason.lower()


def test_orchestrator_luna_departments():
    result = orchestrate_rfp(_read_fixture("luna-cosmetics.md"), use_llm=False)
    assert result.client_country == "US"
    assert "warehouse" in result.departments_needed
    assert "lastmile" in result.departments_needed
    assert "reverse" not in result.departments_needed
    assert result.monthly_volume == 5000


def test_orchestrator_modaviva_departments():
    result = orchestrate_rfp(_read_fixture("modaviva.md"), use_llm=False)
    assert result.client_country == "ES"
    assert set(result.departments_needed) == {"warehouse", "reverse"}


def test_warehouse_worker_key_aspects_and_approver():
    markdown = _read_fixture("luna-cosmetics.md")
    meta = {
        "client_name": "Luna Cosmetics",
        "client_country": "US",
        "monthly_volume": 5000,
        "deadline": "20 days",
    }
    result = run_department_worker("warehouse", markdown=markdown, metadata=meta)
    assert result.approver == "Ana Whitfield"
    assert result.department_id == "warehouse"
    assert len(result.key_aspects) >= 3
    assert any("USD" in aspect or "almacen" in aspect.lower() or "capacidad" in aspect.lower() for aspect in result.key_aspects)


def test_readability_and_cost_estimate():
    text = _read_fixture("luna-cosmetics.md")
    metrics = compute_readability_metrics(text)
    assert metrics["word_count"] > 20
    cost = estimate_processing_cost(metrics)
    assert cost["band"] in {"low", "medium", "high"}
    assert 1 <= cost["score_1_to_5"] <= 5


def test_pdf_roundtrip_extracts_seed_signals():
    text = _read_fixture("carrier-offer.md")
    pdf = build_simple_pdf(text, title="Carrier Offer")
    extracted = pdf_bytes_to_markdown(pdf, filename="carrier-offer.pdf")
    assert "trackflow" in extracted.lower() or "carrier" in extracted.lower()


def test_graph_part1_luna_ends_waiting_approval():
    result = run_rfp_part1(
        ticket_id="t-luna",
        markdown=_read_fixture("luna-cosmetics.md"),
        use_llm=False,
    )
    assert result["is_rfp"] is True
    assert result["status"] == "esperando_aprobación"
    depts = (result.get("metadata") or {}).get("departments_needed") or []
    assert set(depts) == {"warehouse", "lastmile"}
    assert len(result.get("worker_results") or []) == 2
    assert "Ana Whitfield" in (result.get("synthesis_brief") or "")
    assert "Carlos Vega" in (result.get("synthesis_brief") or "")


def test_graph_part1_carrier_offer_discarded():
    result = run_rfp_part1(
        ticket_id="t-offer",
        markdown=_read_fixture("carrier-offer.md"),
        use_llm=False,
    )
    assert result["is_rfp"] is False
    assert result["status"] == "descartado"
    assert result.get("worker_results") in (None, [])
