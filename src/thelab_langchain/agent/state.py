"""
Agent state definition for the LangGraph-powered Supermemory agent.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """The state passed between nodes in the LangGraph agent."""

    # Conversation history (automatically managed by LangGraph with add_messages reducer)
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)

    # Identity & session
    user_id: str = Field(..., description="Supermemory container_tag / user namespace")
    thread_id: str = Field(default="default", description="Persistent session identifier")

    # Long-term memory context (injected by memory nodes)
    long_term_context: str = Field(default="", description="Relevant memories + profile injected into the prompt")

    # Scratchpad for tools / intermediate results
    scratchpad: dict[str, Any] = Field(default_factory=dict)

    # Control flags
    needs_memory_refresh: bool = Field(default=False)
