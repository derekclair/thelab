"""Tests for the LangGraph agent brain: routing and memory injection.

These are pure-logic tests. All external services (Supermemory and the LLM) are
mocked, so the suite needs no network access, API keys, GPU, or audio libraries.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END

from thelab_langchain.agent import graph
from thelab_langchain.agent.graph import _should_continue
from thelab_langchain.agent.state import AgentState


def _state(*messages) -> AgentState:
    return AgentState(user_id="test-user", messages=list(messages))


# --- _should_continue -------------------------------------------------------


def test_should_continue_routes_to_tools_when_tool_calls_present():
    ai = AIMessage(
        content="",
        tool_calls=[
            {"name": "recall_memories", "args": {"query": "hi"}, "id": "call-1", "type": "tool_call"}
        ],
    )
    assert _should_continue(_state(HumanMessage(content="hi"), ai)) == "execute_tools"


def test_should_continue_ends_when_no_tool_calls():
    ai = AIMessage(content="all done, nothing to look up")
    assert _should_continue(_state(HumanMessage(content="hi"), ai)) == END


def test_should_continue_ends_on_non_ai_message():
    # A HumanMessage as the last message must not be routed to tools.
    assert _should_continue(_state(HumanMessage(content="still my turn"))) == END


# --- _memory_injection ------------------------------------------------------


class _FakeTool:
    """Stand-in for a bound Supermemory LangChain tool."""

    def __init__(self, name: str, result: str) -> None:
        self.name = name
        self._result = result
        self.calls: list = []

    def invoke(self, arg):
        self.calls.append(arg)
        return self._result


def test_memory_injection_injects_system_message_without_summarization_llm(monkeypatch):
    profile_tool = _FakeTool("get_user_profile", "## User Profile\n- Likes strong coffee")
    recall_tool = _FakeTool("recall_memories", "- Talked about the DGX Spark voice agent")
    store_tool = _FakeTool("store_memory", "")

    monkeypatch.setattr(
        graph, "create_memory_tools", lambda user_id: [recall_tool, store_tool, profile_tool]
    )

    # If the node ever tried to summarize memory via an LLM round-trip, this fires.
    llm_factory = MagicMock()
    monkeypatch.setattr(graph, "get_chat_model", llm_factory)

    state = _state(HumanMessage(content="What do you know about my project?"))
    result = graph._memory_injection(state)

    messages = result["messages"]
    injected = messages[0]
    assert isinstance(injected, SystemMessage)
    assert "User Context (from long-term memory)" in injected.content
    assert "Likes strong coffee" in injected.content
    assert "DGX Spark voice agent" in injected.content

    # The original conversation is preserved after the injected context.
    assert isinstance(messages[-1], HumanMessage)

    # The node fetched from Supermemory (profile + recall).
    assert profile_tool.calls
    assert recall_tool.calls

    # Latency design point: NO extra summarization LLM round-trip per voice turn.
    llm_factory.assert_not_called()


def test_memory_injection_returns_empty_when_no_context(monkeypatch):
    empty_profile = _FakeTool("get_user_profile", "")
    empty_recall = _FakeTool("recall_memories", "")
    monkeypatch.setattr(graph, "create_memory_tools", lambda user_id: [empty_recall, empty_profile])

    llm_factory = MagicMock()
    monkeypatch.setattr(graph, "get_chat_model", llm_factory)

    result = graph._memory_injection(_state(HumanMessage(content="hello")))

    assert result == {}
    llm_factory.assert_not_called()
