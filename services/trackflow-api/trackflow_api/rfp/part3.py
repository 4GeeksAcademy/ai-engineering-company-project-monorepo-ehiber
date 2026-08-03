"""Parte 3: human-in-the-loop approval per department with checkpointed interrupts."""

from __future__ import annotations

import operator
from functools import lru_cache
from typing import Annotated, Any, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .agents.generators import generate_department_section
from .constants import DEPARTMENT_CATALOG, MAX_HUMAN_APPROVAL_ROUNDS
from .trace import make_trace_entry


class DeptApprovalState(TypedDict, total=False):
    ticket_id: str
    department_id: str
    draft_content: str
    key_aspects: list[str]
    metadata: dict[str, Any]
    human_approval_rounds: int
    decision: str | None
    comment: str | None
    approval_status: str
    arbitration_action: str | None
    node_logs: Annotated[list[dict[str, Any]], operator.add]


def department_thread_id(ticket_id: str, department_id: str) -> str:
    """Scoped thread so one department's pause does not block sibling departments."""
    return f"{ticket_id}::part3::{department_id}"


def _log(
    agent: str,
    *,
    input_payload: Any,
    output_payload: Any,
    department_id: str | None = None,
) -> dict[str, Any]:
    return {
        "node_logs": [
            make_trace_entry(
                agent=agent,
                input_payload=input_payload,
                output_payload=output_payload,
                part=3,
                department_id=department_id,
            )
        ]
    }


def node_prepare(state: DeptApprovalState) -> dict[str, Any]:
    dept = state["department_id"]
    return {
        "approval_status": "pending",
        **_log(
            "prepare_approval",
            input_payload={"department_id": dept, "rounds": state.get("human_approval_rounds", 0)},
            output_payload={"ready_for_interrupt": True},
            department_id=dept,
        ),
    }


def node_await_human_approval(state: DeptApprovalState) -> dict[str, Any]:
    """Pause this department branch until a human resumes with approve/reject."""
    dept = state["department_id"]
    payload = {
        "type": "human_approval",
        "ticket_id": state["ticket_id"],
        "department_id": dept,
        "approver": DEPARTMENT_CATALOG.get(dept, {}).get("approver"),
        "human_approval_rounds": state.get("human_approval_rounds", 0),
        "max_rounds": MAX_HUMAN_APPROVAL_ROUNDS,
        "draft_preview": (state.get("draft_content") or "")[:400],
    }
    decision = interrupt(payload)
    if not isinstance(decision, dict):
        decision = {"action": str(decision), "comment": None}
    action = str(decision.get("action") or "").lower()
    comment = decision.get("comment")
    return {
        "decision": action,
        "comment": comment,
        **_log(
            "await_human_approval",
            input_payload=payload,
            output_payload={"action": action, "comment": comment},
            department_id=dept,
        ),
    }


def node_apply_decision(state: DeptApprovalState) -> dict[str, Any]:
    dept = state["department_id"]
    action = (state.get("decision") or "").lower()
    rounds = int(state.get("human_approval_rounds") or 0)
    comment = state.get("comment")

    if action == "approve":
        return {
            "approval_status": "approved",
            **_log(
                "apply_decision",
                input_payload={"action": action, "comment": comment},
                output_payload={"approval_status": "approved"},
                department_id=dept,
            ),
        }

    if action == "reject":
        rounds += 1
        if rounds >= MAX_HUMAN_APPROVAL_ROUNDS:
            return {
                "human_approval_rounds": rounds,
                "approval_status": "needs_arbitration",
                **_log(
                    "apply_decision",
                    input_payload={"action": action, "rounds": rounds, "limit": MAX_HUMAN_APPROVAL_ROUNDS},
                    output_payload={"approval_status": "needs_arbitration", "reason": "max_rounds"},
                    department_id=dept,
                ),
            }

        feedback = [comment] if comment else ["Rechazo humano: regenerar sección."]
        regenerated = generate_department_section(
            dept,
            metadata=state.get("metadata") or {},
            key_aspects=list(state.get("key_aspects") or []),
            feedback=feedback,
        )
        return {
            "human_approval_rounds": rounds,
            "draft_content": regenerated.draft_content,
            "approval_status": "pending",
            "decision": None,
            "comment": None,
            **_log(
                "apply_decision",
                input_payload={"action": action, "rounds": rounds, "feedback": feedback},
                output_payload={
                    "approval_status": "pending",
                    "regenerated": True,
                    "human_approval_rounds": rounds,
                },
                department_id=dept,
            ),
        }

    return {
        "approval_status": "needs_arbitration",
        **_log(
            "apply_decision",
            input_payload={"action": action},
            output_payload={"approval_status": "needs_arbitration", "reason": "unknown_action"},
            department_id=dept,
        ),
    }


def route_after_decision(
    state: DeptApprovalState,
) -> Literal["await_human_approval", "arbitrate", "end_approved"]:
    status = state.get("approval_status")
    if status == "approved":
        return "end_approved"
    if status == "needs_arbitration":
        return "arbitrate"
    return "await_human_approval"


def node_end_approved(state: DeptApprovalState) -> dict[str, Any]:
    dept = state["department_id"]
    return _log(
        "end_approved",
        input_payload={"department_id": dept},
        output_payload={"approval_status": "approved"},
        department_id=dept,
    )


def node_arbitrate(state: DeptApprovalState) -> dict[str, Any]:
    """Explicit arbitration node for disagreements / exhausted human rounds."""
    dept = state["department_id"]
    payload = {
        "type": "arbitration",
        "ticket_id": state["ticket_id"],
        "department_id": dept,
        "human_approval_rounds": state.get("human_approval_rounds", 0),
        "max_rounds": MAX_HUMAN_APPROVAL_ROUNDS,
        "reason": "department_disagreement_or_max_reject_rounds",
        "options": ["force_approve", "force_reject", "discard_ticket"],
    }
    decision = interrupt(payload)
    if not isinstance(decision, dict):
        decision = {"action": str(decision)}
    action = str(decision.get("action") or "force_reject").lower()

    if action == "force_approve":
        status = "approved"
    elif action == "discard_ticket":
        status = "rejected"
    else:
        status = "rejected"

    return {
        "arbitration_action": action,
        "approval_status": status,
        "decision": action,
        **_log(
            "arbitrate",
            input_payload=payload,
            output_payload={"action": action, "approval_status": status},
            department_id=dept,
        ),
    }


@lru_cache
def get_compiled_dept_approval_graph():
    graph = StateGraph(DeptApprovalState)
    graph.add_node("prepare", node_prepare)
    graph.add_node("await_human_approval", node_await_human_approval)
    graph.add_node("apply_decision", node_apply_decision)
    graph.add_node("end_approved", node_end_approved)
    graph.add_node("arbitrate", node_arbitrate)

    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "await_human_approval")
    graph.add_edge("await_human_approval", "apply_decision")
    graph.add_conditional_edges(
        "apply_decision",
        route_after_decision,
        {
            "await_human_approval": "await_human_approval",
            "arbitrate": "arbitrate",
            "end_approved": "end_approved",
        },
    )
    graph.add_edge("end_approved", END)
    graph.add_edge("arbitrate", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def start_department_approval(
    *,
    ticket_id: str,
    department_id: str,
    draft_content: str,
    key_aspects: list[str],
    metadata: dict[str, Any],
    human_approval_rounds: int = 0,
) -> dict[str, Any]:
    """Run until first interrupt (human approval). Returns interrupt payload + state snapshot."""
    graph = get_compiled_dept_approval_graph()
    config = {"configurable": {"thread_id": department_thread_id(ticket_id, department_id)}}
    result = graph.invoke(
        {
            "ticket_id": ticket_id,
            "department_id": department_id,
            "draft_content": draft_content,
            "key_aspects": key_aspects,
            "metadata": metadata,
            "human_approval_rounds": human_approval_rounds,
            "approval_status": "pending",
            "node_logs": [],
        },
        config=config,
    )
    state = graph.get_state(config)
    interrupts = []
    for task in state.tasks:
        if getattr(task, "interrupts", None):
            interrupts.extend(list(task.interrupts))
    return {
        "interrupted": len(interrupts) > 0,
        "interrupts": [getattr(i, "value", i) for i in interrupts],
        "values": result if isinstance(result, dict) else dict(state.values),
        "next": list(state.next),
    }


def resume_department_approval(
    *,
    ticket_id: str,
    department_id: str,
    action: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Resume exactly from the interrupt point with a human decision."""
    graph = get_compiled_dept_approval_graph()
    config = {"configurable": {"thread_id": department_thread_id(ticket_id, department_id)}}
    result = graph.invoke(
        Command(resume={"action": action, "comment": comment}),
        config=config,
    )
    state = graph.get_state(config)
    interrupts = []
    for task in state.tasks:
        if getattr(task, "interrupts", None):
            interrupts.extend(list(task.interrupts))
    values = result if isinstance(result, dict) else dict(state.values)
    return {
        "interrupted": len(interrupts) > 0,
        "interrupts": [getattr(i, "value", i) for i in interrupts],
        "values": values,
        "next": list(state.next),
        "approval_status": values.get("approval_status"),
        "human_approval_rounds": values.get("human_approval_rounds", 0),
        "draft_content": values.get("draft_content"),
        "arbitration_action": values.get("arbitration_action"),
        "node_logs": list(values.get("node_logs") or []),
    }


def reset_dept_approval_graph_cache() -> None:
    get_compiled_dept_approval_graph.cache_clear()
