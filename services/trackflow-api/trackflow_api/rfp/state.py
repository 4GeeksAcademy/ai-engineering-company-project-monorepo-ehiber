"""LangGraph state for RFP intake (Parte 1)."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class RfpGraphState(TypedDict, total=False):
    ticket_id: str
    markdown: str
    use_llm: bool
    is_rfp: bool
    classifier_reason: str
    classifier_method: str
    metadata: dict[str, Any]
    readability_metrics: dict[str, Any]
    processing_cost_estimate: dict[str, Any]
    worker_results: list[dict[str, Any]]
    synthesis_brief: str
    status: str
    node_trace: Annotated[list[dict[str, Any]], operator.add]
