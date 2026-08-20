"""
LangGraph agent definition for the TheLab voice agent.

This module is responsible for constructing the reasoning brain
that sits behind the voice interface.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from ..llm import get_chat_model
from .state import AgentState
from .tools.memory import create_memory_tools


def _memory_injection(state: AgentState) -> dict:
    """
    Proactively pull relevant long-term memory from Supermemory before the LLM thinks.

    This gives the agent immediate context about the user without requiring the
    model to decide to call tools on every turn.
    """
    user_id = getattr(state, "user_id", "default-user")

    # Get the last user utterance to use as a good recall query
    last_user_msg = ""
    for msg in reversed(state.messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = getattr(msg, "content", str(msg))
            break

    tools = create_memory_tools(user_id)

    # Find the tools by name
    profile_tool = next((t for t in tools if t.name == "get_user_profile"), None)
    recall_tool = next((t for t in tools if t.name == "recall_memories"), None)

    profile_context = ""
    if profile_tool:
        try:
            profile_context = profile_tool.invoke({"query": last_user_msg or None})
        except Exception:
            profile_context = ""

    memory_context = ""
    if recall_tool and last_user_msg:
        try:
            memory_context = recall_tool.invoke({"query": last_user_msg, "limit": 3})
        except Exception:
            memory_context = ""

    combined = ""
    if profile_context:
        combined += profile_context + "\n\n"
    if memory_context:
        combined += f"## Relevant Long-term Memories\n{memory_context}"

    if not combined:
        return {}

    # Inject raw context directly — the main LLM handles it fine and this avoids
    # an extra LLM round-trip that adds 500-1000ms of latency per voice turn.
    injection = SystemMessage(content=f"## User Context (from long-term memory)\n{combined.strip()}")

    # Prepend the injection so it's early context
    return {"messages": [injection] + list(state.messages)}


def _call_llm(state: AgentState, tools: list) -> dict:
    """Call the LLM (with tools bound) on the current messages."""
    llm = get_chat_model()
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(state.messages)
    return {"messages": [response]}


def _execute_tools(state: AgentState, tools: list) -> dict:
    """Execute any tool calls requested by the LLM."""
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)
    return result


def _should_continue(state: AgentState) -> str:
    """Decide whether to continue to tools or end."""
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
        return "execute_tools"
    return END


def build_agent_graph(user_id: str = "default-user") -> StateGraph:
    """
    Build the main LangGraph for the voice agent.

    Architecture:
    - memory_injection (proactive Supermemory context)
    - call_llm (with Supermemory tools bound)
    - execute_tools (if the model requested any)
    - loop back to call_llm if tools were used

    This enables both proactive memory injection and reactive tool use
    (the model can now decide to call store_memory, recall_memories, etc.).
    """
    tools = create_memory_tools(user_id)

    workflow = StateGraph(AgentState)

    # Bind tools into the nodes via closures
    def call_llm(state: AgentState):
        return _call_llm(state, tools)

    def execute_tools(state: AgentState):
        return _execute_tools(state, tools)

    workflow.add_node("memory_injection", _memory_injection)
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("execute_tools", execute_tools)

    workflow.set_entry_point("memory_injection")
    workflow.add_edge("memory_injection", "call_llm")
    workflow.add_conditional_edges("call_llm", _should_continue, {
        "execute_tools": "execute_tools",
        END: END,
    })
    workflow.add_edge("execute_tools", "call_llm")

    return workflow


def get_agent(user_id: str = "default-user"):
    """Returns a compiled runnable LangGraph agent for the given user."""
    graph = build_agent_graph(user_id=user_id)
    return graph.compile()
