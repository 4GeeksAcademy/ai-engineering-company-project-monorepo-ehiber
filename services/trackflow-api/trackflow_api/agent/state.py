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
    intent: str  # rag | incident | inventory
    chunks: list[dict]
    answer: str
    sources: list[dict]
    tool_name: str | None
    tool_result: dict[str, Any] | None
    tool_error: str | None
    error: str | None
    # Append-only step log for queryable traces
    node_trace: Annotated[list[dict], operator.add]
