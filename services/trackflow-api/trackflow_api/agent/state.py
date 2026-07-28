from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    """Minimal explicit state passed between graph nodes.

    Intentionally excludes full chat history — only the current question and
    artifacts produced by single-responsibility nodes.
    """

    run_id: str
    raw_question: str
    question: str
    user_uuid: str | None
    # Optional explicit memory decision from API / UI
    memory_decision: str | None
    memory_proposal_id: str | None
    memory_edited_content: str | None
    memory_decision_result: dict[str, Any] | None
    approved_memories: list[dict]
    memory_proposal: dict[str, Any] | None
    intent: str  # rag | incident | inventory
    guard_decision: str | None
    failure_type: str | None
    guardrail: str | None
    policy_country_lock: str | None
    tracking_id: str | None
    chunks: list[dict]
    answer: str
    sources: list[dict]
    tool_name: str | None
    tool_result: dict[str, Any] | None
    tool_error: str | None
    error: str | None
    # Append-only step log for queryable traces
    node_trace: Annotated[list[dict], operator.add]
