"""
Supermemory operations exposed as LangChain @tool functions.

These become the agent's interface to long-term user memory.
The agent can choose when to recall or store information.

Tools are created via `create_memory_tools(user_id)` so they are properly
scoped per user (critical for future multi-user support).
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field
from supermemory import Supermemory


def _get_memory_client() -> Supermemory:
    """Lazy singleton Supermemory client."""
    api_key = os.getenv("SUPERMEMORY_API_KEY")
    if not api_key:
        raise RuntimeError("SUPERMEMORY_API_KEY must be set in environment")
    return Supermemory(api_key=api_key)


class RecallMemoriesInput(BaseModel):
    query: str = Field(..., description="Semantic search query to find relevant past memories")
    limit: int = Field(default=5, description="Maximum number of memories to return")


class StoreMemoryInput(BaseModel):
    content: str = Field(..., description="The memory content to store permanently")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional structured metadata (tags, project, type, etc.)"
    )


class GetProfileInput(BaseModel):
    query: str | None = Field(
        default=None,
        description="Optional query to also pull relevant memories alongside the profile",
    )


def create_memory_tools(user_id: str) -> list[BaseTool]:
    """
    Factory that returns Supermemory tools bound to a specific user.

    This is the recommended way to create the tools so they are
    correctly isolated per user (supports multi-user households).
    """
    client = _get_memory_client()

    @tool("recall_memories", args_schema=RecallMemoriesInput)
    def recall_memories(query: str, limit: int = 5) -> str:
        """Search the user's long-term memory for relevant past conversations, facts, and context."""
        results = client.search.memories(
            q=query,
            container_tag=user_id,
            limit=limit,
        )
        if not results or not getattr(results, "results", None):
            return "No relevant memories found for this query."

        formatted = []
        for r in results.results:
            text = getattr(r, "memory", None) or getattr(r, "chunk", None) or str(r)
            if text:
                formatted.append(f"- {text}")
        return "\n".join(formatted[:limit])

    @tool("store_memory", args_schema=StoreMemoryInput)
    def store_memory(content: str, metadata: dict[str, Any] | None = None) -> str:
        """Store important information about the user into long-term memory."""
        client.add(
            content=content,
            container_tag=user_id,
            metadata=metadata or {},
        )
        return f"Successfully stored memory: {content[:100]}..."

    @tool("get_user_profile", args_schema=GetProfileInput)
    def get_user_profile(query: str | None = None) -> str:
        """Retrieve the user's automatically generated long-term profile and relevant memories."""
        result = client.profile(
            container_tag=user_id,
            q=query or "current context and preferences",
        )
        profile = getattr(result, "profile", None) or {}
        static = getattr(profile, "static", None) or []
        dynamic = getattr(profile, "dynamic", None) or []

        lines = ["## User Profile"]
        if static:
            lines.append("\n### Long-term Facts")
            lines.extend(f"- {s}" for s in static)
        if dynamic:
            lines.append("\n### Recent Activity & Focus")
            lines.extend(f"- {d}" for d in dynamic)

        if len(lines) == 1:
            return "No profile information available yet for this user."
        return "\n".join(lines)

    return [recall_memories, store_memory, get_user_profile]
