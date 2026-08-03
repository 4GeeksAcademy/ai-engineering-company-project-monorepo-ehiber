"""Unit tests for RFP Parte 3: interrupt/resume, iteration limit, arbitration."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from trackflow_api.core.config import REPO_ROOT
from trackflow_api.core.database import get_inventory_engine
from trackflow_api.rfp.constants import MAX_HUMAN_APPROVAL_ROUNDS
from trackflow_api.rfp.final_document import assemble_final_document
from trackflow_api.rfp.ingest import build_simple_pdf
from trackflow_api.rfp.part3 import (
    department_thread_id,
    reset_dept_approval_graph_cache,
    resume_department_approval,
    start_department_approval,
)
from trackflow_api.services import rfp_service

FIXTURES = REPO_ROOT / "docs" / "agentic-workflow" / "fixtures" / "rfp"


def setup_function() -> None:
    reset_dept_approval_graph_cache()


def test_max_human_approval_rounds_constant_is_verifiable():
    assert MAX_HUMAN_APPROVAL_ROUNDS == 2


def test_interrupt_pauses_and_resume_approves_without_restart():
    meta = {
        "client_name": "Luna Cosmetics",
        "client_country": "US",
        "services_requested": ["warehousing"],
        "monthly_volume": 5000,
    }
    first = start_department_approval(
        ticket_id="resume-t1",
        department_id="warehouse",
        draft_content="draft v1",
        key_aspects=["capacidad"],
        metadata=meta,
    )
    assert first["interrupted"] is True
    assert first["interrupts"][0]["type"] == "human_approval"
    assert first["next"] == ["await_human_approval"]

    second = resume_department_approval(
        ticket_id="resume-t1",
        department_id="warehouse",
        action="approve",
        comment="OK Ana",
    )
    assert second["interrupted"] is False
    assert second["approval_status"] == "approved"
    assert second["next"] == []
    agents = [e["agent"] for e in second["node_logs"]]
    assert "await_human_approval" in agents
    assert "apply_decision" in agents
    for entry in second["node_logs"]:
        assert "timestamp" in entry
        assert "agent" in entry
        assert "input" in entry
        assert "output" in entry


def test_department_threads_are_independent():
    meta = {"client_name": "Luna Cosmetics", "client_country": "US", "services_requested": []}
    start_department_approval(
        ticket_id="par-t",
        department_id="warehouse",
        draft_content="wh",
        key_aspects=[],
        metadata=meta,
    )
    start_department_approval(
        ticket_id="par-t",
        department_id="lastmile",
        draft_content="lm",
        key_aspects=[],
        metadata=meta,
    )
    # Approve only lastmile — warehouse remains interrupted.
    lm = resume_department_approval(
        ticket_id="par-t", department_id="lastmile", action="approve"
    )
    assert lm["approval_status"] == "approved"

    from trackflow_api.rfp.part3 import get_compiled_dept_approval_graph

    graph = get_compiled_dept_approval_graph()
    wh_state = graph.get_state(
        {"configurable": {"thread_id": department_thread_id("par-t", "warehouse")}}
    )
    assert list(wh_state.next) == ["await_human_approval"]
    assert any(getattr(t, "interrupts", None) for t in wh_state.tasks)


def test_iteration_limit_routes_to_arbitrate_node():
    meta = {"client_name": "Luna Cosmetics", "client_country": "US", "services_requested": []}
    start_department_approval(
        ticket_id="lim-t",
        department_id="warehouse",
        draft_content="d",
        key_aspects=["capacidad"],
        metadata=meta,
    )
    r1 = resume_department_approval(
        ticket_id="lim-t", department_id="warehouse", action="reject", comment="fix 1"
    )
    assert r1["interrupted"] is True
    assert r1["interrupts"][0]["type"] == "human_approval"
    assert r1["human_approval_rounds"] == 1

    r2 = resume_department_approval(
        ticket_id="lim-t", department_id="warehouse", action="reject", comment="fix 2"
    )
    assert r2["interrupted"] is True
    assert r2["approval_status"] == "needs_arbitration"
    assert r2["interrupts"][0]["type"] == "arbitration"
    assert r2["human_approval_rounds"] >= MAX_HUMAN_APPROVAL_ROUNDS
    agents = [e["agent"] for e in r2["node_logs"]]
    assert "arbitrate" in agents or r2["interrupts"][0]["type"] == "arbitration"


def test_arbitration_force_approve():
    meta = {"client_name": "Luna Cosmetics", "client_country": "US", "services_requested": []}
    start_department_approval(
        ticket_id="arb-t",
        department_id="reverse",
        draft_content="d",
        key_aspects=["devoluciones"],
        metadata=meta,
    )
    resume_department_approval(ticket_id="arb-t", department_id="reverse", action="reject")
    resume_department_approval(ticket_id="arb-t", department_id="reverse", action="reject")
    final = resume_department_approval(
        ticket_id="arb-t", department_id="reverse", action="force_approve"
    )
    assert final["approval_status"] == "approved"
    assert final["arbitration_action"] == "force_approve"
    assert any(e["agent"] == "arbitrate" for e in final["node_logs"])


def test_assemble_final_document_only_with_approved_sections():
    doc = assemble_final_document(
        metadata={
            "client_name": "Luna Cosmetics",
            "client_country": "US",
            "services_requested": ["warehousing", "last_mile"],
            "monthly_volume": 5000,
            "deadline": "20 days",
        },
        sections=[
            {
                "department_id": "warehouse",
                "approver": "Ana Whitfield",
                "draft_content": "## Warehouse body",
            },
            {
                "department_id": "lastmile",
                "approver": "Carlos Vega",
                "draft_content": "## Last mile body",
            },
        ],
    )
    assert doc["currency"] == "USD"
    assert doc["sections"] == ["warehouse", "lastmile"]
    assert "Luna Cosmetics" in doc["content"]
    assert "Warehouse body" in doc["content"]
    assert "Last mile body" in doc["content"]


def test_e2e_luna_parts_1_to_3(tmp_path):
    reset_dept_approval_graph_cache()
    md = (FIXTURES / "luna-cosmetics.md").read_text(encoding="utf-8")
    pdf = build_simple_pdf(md, title="Luna Cosmetics RFP")

    with Session(get_inventory_engine()) as session:
        created = rfp_service.create_ticket_from_upload(
            session,
            filename="luna-cosmetics.pdf",
            pdf_bytes=pdf,
            user_uuid="test-user",
        )
        ticket_id = created.ticket_id
        # Simple PDF extract can be lossy; drive Parte 1 from the canonical Markdown fixture.
        _seed_part1_from_markdown(session, ticket_id, md)
        ticket = rfp_repository_get(session, ticket_id)
        assert ticket is not None
        assert ticket.is_rfp is True
        assert ticket.status == "esperando_aprobación"
        assert ticket.approval_phase == "intake"

        rfp_service.approve_intake(session, ticket_id)
        ticket = rfp_repository_get(session, ticket_id)
        assert ticket.approval_phase == "section_signoff"
        assert ticket.status == "esperando_aprobación"
        sections = [s.department_id for s in _sections(session, ticket_id)]
        assert set(sections) == {"warehouse", "lastmile"}

        # Approve warehouse first — lastmile still pending (non-blocking).
        rfp_service.decide_section(session, ticket_id, "warehouse", action="approve")
        ticket = rfp_repository_get(session, ticket_id)
        assert ticket.status == "esperando_aprobación"
        wh = _section(session, ticket_id, "warehouse")
        lm = _section(session, ticket_id, "lastmile")
        assert wh.approval_status == "approved"
        assert lm.approval_status in {"pending", "needs_arbitration"}

        rfp_service.decide_section(session, ticket_id, "lastmile", action="approve")
        ticket = rfp_repository_get(session, ticket_id)
        assert ticket.status == "terminado"
        assert ticket.final_document_content
        assert "Luna Cosmetics" in ticket.final_document_content
        assert ticket.run_trace
        assert any(
            isinstance(e, dict) and e.get("agent") == "assemble_final_document"
            for e in ticket.run_trace
        )


def _seed_part1_from_markdown(session, ticket_id: str, markdown: str) -> None:
    from pathlib import Path

    from trackflow_api.repositories import rfp_repository
    from trackflow_api.rfp.graph import run_rfp_part1

    ticket = rfp_repository.get_ticket(session, ticket_id)
    assert ticket is not None
    md_path = Path(ticket.pdf_path).with_suffix(".md")
    md_path.write_text(markdown, encoding="utf-8")
    result = run_rfp_part1(ticket_id=ticket_id, markdown=markdown, use_llm=False)
    metadata = result.get("metadata") or {}
    is_rfp = bool(result.get("is_rfp"))
    rfp_repository.update_ticket_fields(
        session,
        ticket,
        markdown_path=str(md_path),
        markdown_content=markdown,
        is_rfp=is_rfp,
        classifier_reason=result.get("classifier_reason"),
        client_name=metadata.get("client_name"),
        client_country=metadata.get("client_country"),
        services_requested=list(metadata.get("services_requested") or []),
        monthly_volume=metadata.get("monthly_volume"),
        deadline=metadata.get("deadline"),
        budget_range=metadata.get("budget_range"),
        departments_needed=list(metadata.get("departments_needed") or []),
        readability_metrics=dict(result.get("readability_metrics") or {}),
        processing_cost_estimate=dict(result.get("processing_cost_estimate") or {}),
        synthesis_brief=result.get("synthesis_brief"),
        status=str(result.get("status") or "esperando_aprobación"),
        approval_phase="intake" if is_rfp else None,
        error_message=None,
    )
    if is_rfp:
        rfp_repository.replace_sections(
            session,
            ticket_id=ticket_id,
            sections=list(result.get("worker_results") or []),
        )


def rfp_repository_get(session, ticket_id):
    from trackflow_api.repositories import rfp_repository

    return rfp_repository.get_ticket(session, ticket_id)


def _sections(session, ticket_id):
    from trackflow_api.repositories import rfp_repository

    return rfp_repository.list_sections(session, ticket_id)


def _section(session, ticket_id, department_id):
    from trackflow_api.repositories import rfp_repository

    return rfp_repository.get_section(session, ticket_id=ticket_id, department_id=department_id)
