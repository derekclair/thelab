"""Memory-aware chat using LangChain (Grok/Anthropic) + Supermemory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from rich.console import Console
from rich.panel import Panel
from supermemory import Supermemory

from .config import settings
from .llm import get_chat_model

console = Console()


@dataclass
class MemoryContext:
    """Structured context returned from Supermemory profile + search."""

    static_facts: list[str] = field(default_factory=list)
    dynamic_context: list[str] = field(default_factory=list)
    relevant_memories: list[str] = field(default_factory=list)
    raw: Any = None  # original Supermemory result for advanced use

    def to_prompt_block(self) -> str:
        """Format as a readable context block for the system prompt."""
        lines: list[str] = ["## User Memory Context"]

        if self.static_facts:
            lines.append("\n### Long-term Profile")
            lines.extend(f"- {fact}" for fact in self.static_facts)

        if self.dynamic_context:
            lines.append("\n### Recent Activity")
            lines.extend(f"- {ctx}" for ctx in self.dynamic_context)

        if self.relevant_memories:
            lines.append("\n### Relevant Past Memories")
            lines.extend(f"- {mem}" for mem in self.relevant_memories[:6])

        if len(lines) == 1:
            lines.append("No prior memories or profile for this user yet.")

        return "\n".join(lines)


class MemoryChat:
    """Conversational agent that uses Supermemory for long-term recall and LangChain for reasoning."""

    def __init__(self, user_id: str | None = None) -> None:
        settings.validate_keys()

        self.user_id = user_id or settings.default_user_id
        self.memory = Supermemory(api_key=settings.supermemory_api_key.get_secret_value())

        # Initialize the chosen LLM using the central factory (supports xai, anthropic, openai_compatible)
        self.llm = get_chat_model()

        if settings.llm_provider == "xai":
            self.provider_name = "Grok (xAI)"
        elif settings.llm_provider == "anthropic":
            self.provider_name = "Claude (Anthropic)"
        else:
            self.provider_name = f"Local ({settings.llm_model})"

        self.conversation: list[HumanMessage | AIMessage] = []

    def _get_memory_context(self, query: str) -> MemoryContext:
        """Fetch profile + semantically relevant memories for the current query."""
        try:
            result = self.memory.profile(
                container_tag=self.user_id,
                q=query,
                threshold=0.55,
            )
        except Exception as exc:  # Supermemory errors are usually network / auth
            console.print(f"[red]Supermemory error:[/red] {exc}")
            return MemoryContext()

        profile = getattr(result, "profile", None) or {}
        search_results = getattr(result, "search_results", None)

        static = getattr(profile, "static", None) or []
        dynamic = getattr(profile, "dynamic", None) or []

        memories: list[str] = []
        if search_results and getattr(search_results, "results", None):
            for r in search_results.results:
                text = getattr(r, "memory", None) or getattr(r, "chunk", None) or str(r)
                if text:
                    memories.append(text)

        return MemoryContext(
            static_facts=static,
            dynamic_context=dynamic,
            relevant_memories=memories,
            raw=result,
        )

    def _build_prompt(self, user_message: str, memory_ctx: MemoryContext) -> list[SystemMessage | HumanMessage | AIMessage]:
        """Construct the full message list for the LLM including memory context."""
        system_content = f"""You are a helpful, thoughtful assistant with excellent long-term memory.

You are powered by {self.provider_name} and backed by Supermemory for persistent user context.

{memory_ctx.to_prompt_block()}

Instructions:
- Use the memory context above to personalize your answers.
- Reference past facts, preferences, or conversations naturally when relevant.
- If the user is new, be friendly and help them build their profile by asking light questions.
- Never mention the internal "memory context" or Supermemory directly unless the user asks.
- Be concise but warm.
"""

        messages: list[SystemMessage | HumanMessage | AIMessage] = [
            SystemMessage(content=system_content.strip())
        ]
        messages.extend(self.conversation[-10:])  # keep recent turns for coherence
        messages.append(HumanMessage(content=user_message))
        return messages

    def chat(self, message: str) -> str:
        """Process a user message, recall memory, call LLM, and persist the turn."""
        console.print(f"\n[dim]Fetching memory for user '{self.user_id}'...[/dim]")
        memory_ctx = self._get_memory_context(message)

        # Show a tiny summary of what memory we got (for demo transparency)
        if memory_ctx.static_facts or memory_ctx.dynamic_context or memory_ctx.relevant_memories:
            summary = (
                f"[green]✓[/green] Profile: {len(memory_ctx.static_facts)} static, "
                f"{len(memory_ctx.dynamic_context)} dynamic, "
                f"{len(memory_ctx.relevant_memories)} relevant memories pulled."
            )
            console.print(summary)

        prompt_messages = self._build_prompt(message, memory_ctx)

        console.print(f"[dim]Calling {self.provider_name} ({settings.llm_model})...[/dim]")
        response: AIMessage = self.llm.invoke(prompt_messages)  # type: ignore[assignment]

        # Persist to long-term memory
        try:
            self.memory.add(
                content=f"User: {message}\nAssistant: {response.content}",
                container_tag=self.user_id,
                metadata={
                    "provider": settings.llm_provider,
                    "model": settings.llm_model,
                    "type": "conversation_turn",
                },
            )
        except Exception as exc:
            console.print(f"[yellow]Warning: failed to store memory: {exc}[/yellow]")

        # Update local conversation buffer
        self.conversation.append(HumanMessage(content=message))
        self.conversation.append(response)

        return response.content

    def show_profile(self) -> None:
        """Debug helper: dump the current Supermemory profile for the user."""
        result = self.memory.profile(container_tag=self.user_id, q="overview")
        profile = getattr(result, "profile", None)

        console.print(Panel.fit(
            f"[bold]User:[/bold] {self.user_id}\n\n"
            f"[bold]Static facts:[/bold]\n{chr(10).join(profile.static or ['(none)'])}\n\n"
            f"[bold]Dynamic context:[/bold]\n{chr(10).join(profile.dynamic or ['(none)'])}",
            title="Supermemory Profile",
            border_style="cyan",
        ))

    def clear_session(self) -> None:
        """Clear only the in-memory conversation (long-term memory stays in Supermemory)."""
        self.conversation = []
        console.print("[yellow]Local conversation buffer cleared. Long-term memory intact.[/yellow]")
