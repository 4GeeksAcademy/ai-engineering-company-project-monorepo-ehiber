"""LangGraph orchestrator-worker-synthesizer for RFP Parte 1."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from .agents.classifier import classify_document
from .agents.orchestrator import orchestrate_rfp
from .agents.synthesizer import synthesize_sales_brief
from .agents.workers import WorkerResult, run_workers_parallel
from .ingest import compute_readability_metrics, estimate_processing_cost
from .state import RfpGraphState


def _trace(node: str, **detail: Any) -> dict[str, Any]:
    return {"node": node, "detail": detail}


def node_ingest_metrics(state: RfpGraphState) -> dict[str, Any]:
    metrics = compute_readability_metrics(state.get("markdown") or "")
    cost = estimate_processing_cost(metrics)
    return {
        "readability_metrics": metrics,
        "processing_cost_estimate": cost,
        "node_trace": [_trace("ingest_metrics", words=metrics.get("word_count"), band=cost.get("band"))],
    }


def node_classify(state: RfpGraphState) -> dict[str, Any]:
    result = classify_document(state.get("markdown") or "", use_llm=bool(state.get("use_llm", False)))
    status = "analizando" if result.is_rfp else "descartado"
    return {
        "is_rfp": result.is_rfp,
        "classifier_reason": result.reason,
        "classifier_method": result.method,
        "status": status,
        "node_trace": [
            _trace(
                "classifier",
                is_rfp=result.is_rfp,
                confidence=result.confidence,
                method=result.method,
            )
        ],
    }


def route_after_classify(state: RfpGraphState) -> Literal["orchestrator", "end_discarded"]:
    if state.get("is_rfp"):
        return "orchestrator"
    return "end_discarded"


def node_end_discarded(state: RfpGraphState) -> dict[str, Any]:
    return {
        "status": "descartado",
        "synthesis_brief": (
            "# Documento descartado\n\n"
            f"{state.get('classifier_reason') or 'No es una RFP de cliente TrackFlow.'}\n"
        ),
        "worker_results": [],
        "metadata": {},
        "node_trace": [_trace("end_discarded")],
    }


def node_orchestrator(state: RfpGraphState) -> dict[str, Any]:
    result = orchestrate_rfp(state.get("markdown") or "", use_llm=bool(state.get("use_llm", False)))
    metadata = {
        "client_name": result.client_name,
        "client_country": result.client_country,
        "services_requested": result.services_requested,
        "monthly_volume": result.monthly_volume,
        "deadline": result.deadline,
        "budget_range": result.budget_range,
        "departments_needed": result.departments_needed,
    }
    return {
        "metadata": metadata,
        "node_trace": [
            _trace(
                "orchestrator",
                departments=result.departments_needed,
                country=result.client_country,
                method=result.method,
            )
        ],
    }


def node_workers(state: RfpGraphState) -> dict[str, Any]:
    metadata = state.get("metadata") or {}
    departments = list(metadata.get("departments_needed") or [])
    workers = run_workers_parallel(
        departments,
        markdown=state.get("markdown") or "",
        metadata=metadata,
    )
    serialized = [
        {
            "department_id": w.department_id,
            "approver": w.approver,
            "key_aspects": w.key_aspects,
            "method": w.method,
        }
        for w in workers
    ]
    return {
        "worker_results": serialized,
        "node_trace": [_trace("workers", departments=[w.department_id for w in workers])],
    }


def node_synthesizer(state: RfpGraphState) -> dict[str, Any]:
    metadata = state.get("metadata") or {}
    raw_workers = state.get("worker_results") or []
    workers = [
        WorkerResult(
            department_id=item["department_id"],
            approver=item["approver"],
            key_aspects=list(item.get("key_aspects") or []),
            method=str(item.get("method") or "heuristic"),
        )
        for item in raw_workers
    ]
    brief = synthesize_sales_brief(
        metadata=metadata,
        workers=workers,
        readability=state.get("readability_metrics"),
        cost_estimate=state.get("processing_cost_estimate"),
    )
    return {
        "synthesis_brief": brief,
        "status": "esperando_aprobación",
        "node_trace": [_trace("synthesizer", sections=len(workers))],
    }


@lru_cache
def get_compiled_rfp_graph():
    graph = StateGraph(RfpGraphState)
    graph.add_node("ingest_metrics", node_ingest_metrics)
    graph.add_node("classifier", node_classify)
    graph.add_node("end_discarded", node_end_discarded)
    graph.add_node("orchestrator", node_orchestrator)
    graph.add_node("workers", node_workers)
    graph.add_node("synthesizer", node_synthesizer)

    graph.add_edge(START, "ingest_metrics")
    graph.add_edge("ingest_metrics", "classifier")
    graph.add_conditional_edges(
        "classifier",
        route_after_classify,
        {
            "orchestrator": "orchestrator",
            "end_discarded": "end_discarded",
        },
    )
    graph.add_edge("end_discarded", END)
    graph.add_edge("orchestrator", "workers")
    graph.add_edge("workers", "synthesizer")
    graph.add_edge("synthesizer", END)
    return graph.compile()


def run_rfp_part1(
    *,
    ticket_id: str,
    markdown: str,
    use_llm: bool = False,
) -> RfpGraphState:
    graph = get_compiled_rfp_graph()
    result = graph.invoke(
        {
            "ticket_id": ticket_id,
            "markdown": markdown,
            "use_llm": use_llm,
            "node_trace": [],
        }
    )
    return result  # type: ignore[return-value]
