"""Tests for MemoryContext.to_prompt_block formatting (pure, no services)."""

from __future__ import annotations

from thelab_langchain.chat import MemoryContext


def test_to_prompt_block_empty_context():
    block = MemoryContext().to_prompt_block()

    assert block.startswith("## User Memory Context")
    assert "No prior memories or profile for this user yet." in block


def test_to_prompt_block_with_all_fields():
    ctx = MemoryContext(
        static_facts=["Prefers concise answers"],
        dynamic_context=["Building a voice agent on DGX Spark"],
        relevant_memories=["Discussed Supermemory integration last week"],
    )
    block = ctx.to_prompt_block()

    assert "### Long-term Profile" in block
    assert "Prefers concise answers" in block
    assert "### Recent Activity" in block
    assert "Building a voice agent on DGX Spark" in block
    assert "### Relevant Past Memories" in block
    assert "Discussed Supermemory integration last week" in block
    assert "No prior memories" not in block
