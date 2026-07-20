from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    abort_invalid,
    generate_answer,
    generate_no_context,
    receive_question,
    retrieve_context,
    route_after_receive,
    route_after_retrieve,
)
from .state import AgentState


def build_knowledge_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("receive_question", receive_question)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("generate_no_context", generate_no_context)
    graph.add_node("abort_invalid", abort_invalid)

    graph.add_edge(START, "receive_question")
    graph.add_conditional_edges(
        "receive_question",
        route_after_receive,
        {
            "retrieve": "retrieve",
            "abort_invalid": "abort_invalid",
        },
    )
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "generate_answer": "generate_answer",
            "generate_no_context": "generate_no_context",
        },
    )
    graph.add_edge("generate_answer", END)
    graph.add_edge("generate_no_context", END)
    graph.add_edge("abort_invalid", END)
    return graph


@lru_cache
def get_compiled_knowledge_graph():
    """Compile once at process start so structural errors fail fast."""
    checkpointer = MemorySaver()
    return build_knowledge_graph().compile(checkpointer=checkpointer)


def reset_compiled_knowledge_graph() -> None:
    get_compiled_knowledge_graph.cache_clear()
