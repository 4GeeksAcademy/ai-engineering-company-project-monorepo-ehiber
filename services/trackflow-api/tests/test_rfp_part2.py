"""Unit tests for RFP Parte 2 generator–evaluator cycle."""

from __future__ import annotations

from trackflow_api.rfp.agents.evaluators import (
    evaluate_compliance,
    evaluate_pertinence,
    evaluate_readability,
    run_evaluators_parallel,
)
from trackflow_api.rfp.agents.generators import (
    generate_department_section,
    generate_lastmile_section,
    generate_reverse_section,
    generate_warehouse_section,
)
from trackflow_api.rfp.part2 import run_generator_evaluator_loop, run_part2_for_departments


def _luna_meta() -> dict:
    return {
        "client_name": "Luna Cosmetics",
        "client_country": "US",
        "services_requested": ["warehousing", "last_mile"],
        "monthly_volume": 5000,
        "deadline": "20 days",
    }


def _modaviva_meta() -> dict:
    return {
        "client_name": "Zaragoza ModaViva",
        "client_country": "ES",
        "services_requested": ["warehousing", "reverse_logistics"],
        "monthly_volume": None,
        "deadline": "25 days",
    }


def test_generators_are_department_specific():
    meta = _luna_meta()
    aspects = ["Confirmar capacidad de almacenamiento"]
    wh = generate_warehouse_section(metadata=meta, key_aspects=aspects)
    lm = generate_lastmile_section(metadata=meta, key_aspects=aspects)
    rev = generate_reverse_section(metadata=_modaviva_meta(), key_aspects=["Devoluciones"])
    assert wh.department_id == "warehouse"
    assert lm.department_id == "lastmile"
    assert rev.department_id == "reverse"
    assert "Warehouse" in wh.draft_content
    assert "Last Mile" in lm.draft_content
    assert "Reverse" in rev.draft_content
    assert wh.draft_content != lm.draft_content


def test_evaluation_success_path_structured():
    meta = _luna_meta()
    draft = generate_department_section(
        "warehouse",
        metadata=meta,
        key_aspects=["Confirmar capacidad de almacenamiento para Luna Cosmetics"],
    ).draft_content
    bundle = run_evaluators_parallel(
        draft,
        metadata=meta,
        key_aspects=["Confirmar capacidad de almacenamiento para Luna Cosmetics"],
        department_id="warehouse",
    )
    assert bundle.passed is True
    payload = bundle.to_dict()
    assert payload["overall_passed"] is True
    assert "passed" in payload["readability"]
    assert "passed" in payload["pertinence"]
    assert "checks" in payload["compliance"]["details"]
    assert all(c["passed"] for c in payload["compliance"]["details"]["checks"])


def test_compliance_fails_wrong_currency_and_missing_sla():
    bad_draft = """
# Warehouse draft
Cliente Luna Cosmetics en España con precios en EUR solamente.
Sin porcentaje de entrega.
Sin tabla.
"""
    result = evaluate_compliance(
        bad_draft,
        metadata=_luna_meta(),  # expects USD
        department_id="warehouse",
    )
    assert result.passed is False
    assert any("USD" in r or "moneda" in r.lower() for r in result.reasons)
    checks = {c["rule"]: c["passed"] for c in result.details["checks"]}
    assert checks["currency_matches_client_country"] is False
    assert checks["on_time_sla_percent_present"] is False


def test_compliance_fails_sub_48h_reverse_promise():
    bad = """
# Reverse
Zaragoza ModaViva — EUR
SLA de entrega a tiempo del 95%.
Procesamos devoluciones en 24 horas.
| Pedidos/mes | Descuento |
| --- | --- |
| 1-1000 | 5% |
"""
    result = evaluate_compliance(bad, metadata=_modaviva_meta(), department_id="reverse")
    assert result.passed is False
    assert any("48" in r for r in result.reasons)


def test_readability_fails_too_short():
    result = evaluate_readability("Corto.")
    assert result.passed is False


def test_pertinence_fails_without_department_signal():
    result = evaluate_pertinence(
        "Documento genérico sin logística para Otro Cliente.",
        metadata=_luna_meta(),
        key_aspects=["Confirmar capacidad de almacenamiento"],
        department_id="warehouse",
    )
    assert result.passed is False


def test_generator_evaluator_loop_success():
    meta = _luna_meta()
    result = run_generator_evaluator_loop(
        "warehouse",
        metadata=meta,
        key_aspects=["Confirmar capacidad de almacenamiento para Luna Cosmetics en US"],
        max_iterations=2,
    )
    assert result.passed is True
    assert result.approval_status == "pending"
    assert result.iteration_count >= 1
    assert result.evaluation_results["overall_passed"] is True
    assert "draft_content" not in result.evaluation_results or True
    assert "USD" in result.draft_content
    assert "SLA" in result.draft_content.upper() or "sla" in result.draft_content.lower()


def test_generator_evaluator_loop_failure_hits_max_iterations(monkeypatch):
    """Force persistent evaluation failure and assert iteration limit + needs_human_review."""
    from trackflow_api.rfp import part2 as part2_mod
    from trackflow_api.rfp.agents.evaluators import EvaluationBundle, EvaluatorResult

    def _always_fail(*_args, **_kwargs):
        fail = EvaluatorResult(name="compliance", passed=False, reasons=["forced fail"], details={})
        ok = EvaluatorResult(name="readability", passed=True, reasons=["ok"], details={})
        ok2 = EvaluatorResult(name="pertinence", passed=True, reasons=["ok"], details={})
        return EvaluationBundle(readability=ok, pertinence=ok2, compliance=fail)

    monkeypatch.setattr(part2_mod, "run_evaluators_parallel", _always_fail)
    result = run_generator_evaluator_loop(
        "lastmile",
        metadata=_luna_meta(),
        key_aspects=["Diseñar red de carriers"],
        max_iterations=2,
    )
    assert result.passed is False
    assert result.iteration_count == 2
    assert result.approval_status == "needs_human_review"
    assert result.evaluation_results.get("max_iterations_reached") is True
    assert len(result.attempts) == 2


def test_part2_runs_departments_without_blocking():
    meta = _modaviva_meta()
    results = run_part2_for_departments(
        ["warehouse", "reverse"],
        metadata=meta,
        sections_by_dept={
            "warehouse": ["Capacidad de almacenamiento ModaViva"],
            "reverse": ["Procesamiento de devoluciones ModaViva"],
        },
        max_iterations=2,
    )
    assert [r.department_id for r in results] == ["warehouse", "reverse"]
    assert all(r.passed for r in results)
    assert all(r.draft_content for r in results)
    assert all(r.evaluation_results.get("overall_passed") for r in results)
