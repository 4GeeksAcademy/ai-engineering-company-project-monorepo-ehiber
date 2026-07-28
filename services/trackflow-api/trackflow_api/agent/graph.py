from __future__ import annotations

from functools import lru_cache

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    abort_invalid,
    authorize_tracking_access,
    classify_question,
    generate_answer,
    generate_from_tool,
    generate_no_context,
    guard_input,
    receive_question,
    redirect_off_topic,
    reject_guardrail,
    retrieve_context,
    route_after_authorize,
    route_after_classify,
    route_after_guard_input,
    route_after_receive,
    route_after_retrieve,
    route_after_tool,
    tool_incidents,
    tool_inventory,
    tool_recovery,
)
from .state import AgentState


def build_knowledge_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("receive_question", receive_question)
    graph.add_node("guard_input", guard_input)
    graph.add_node("authorize_tracking", authorize_tracking_access)
    graph.add_node("reject_guardrail", reject_guardrail)
    graph.add_node("redirect_off_topic", redirect_off_topic)
    graph.add_node("classify_intent", classify_question)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("tool_incidents", tool_incidents)
    graph.add_node("tool_inventory", tool_inventory)
    graph.add_node("tool_recovery", tool_recovery)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("generate_no_context", generate_no_context)
    graph.add_node("generate_from_tool", generate_from_tool)
    graph.add_node("abort_invalid", abort_invalid)

    graph.add_edge(START, "receive_question")
    graph.add_conditional_edges(
        "receive_question",
        route_after_receive,
        {
            "guard_input": "guard_input",
            "abort_invalid": "abort_invalid",
        },
    )
    graph.add_conditional_edges(
        "guard_input",
        route_after_guard_input,
        {
            "reject_guardrail": "reject_guardrail",
            "redirect_off_topic": "redirect_off_topic",
            "authorize_tracking": "authorize_tracking",
        },
    )
    graph.add_conditional_edges(
        "authorize_tracking",
        route_after_authorize,
        {
            "reject_guardrail": "reject_guardrail",
            "classify_intent": "classify_intent",
        },
    )
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "retrieve": "retrieve",
            "tool_incidents": "tool_incidents",
            "tool_inventory": "tool_inventory",
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
    graph.add_conditional_edges(
        "tool_incidents",
        route_after_tool,
        {
            "generate_from_tool": "generate_from_tool",
            "tool_recovery": "tool_recovery",
        },
    )
    graph.add_conditional_edges(
        "tool_inventory",
        route_after_tool,
        {
            "generate_from_tool": "generate_from_tool",
            "tool_recovery": "tool_recovery",
        },
    )
    graph.add_edge("tool_recovery", "generate_from_tool")
    graph.add_edge("generate_answer", END)
    graph.add_edge("generate_no_context", END)
    graph.add_edge("generate_from_tool", END)
    graph.add_edge("reject_guardrail", END)
    graph.add_edge("redirect_off_topic", END)
    graph.add_edge("abort_invalid", END)
    return graph


@lru_cache
def get_compiled_knowledge_graph():
    """Compile once at process start so structural errors fail fast."""
    checkpointer = MemorySaver()
    return build_knowledge_graph().compile(checkpointer=checkpointer)


def reset_compiled_knowledge_graph() -> None:
    get_compiled_knowledge_graph.cache_clear()
