"""Interactive CLI for the LangChain + Supermemory demo."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .chat import MemoryChat
from .config import settings

# VoiceOrchestrator is imported lazily inside the `voice` command
# so that `thelab-chat chat` and `--help` do not require audio dependencies (sounddevice, etc.).

app = typer.Typer(
    name="thelab-chat",
    help="LangChain + Supermemory chat demo (Grok or Claude)",
    add_completion=False,
)
console = Console()


def _print_welcome() -> None:
    base_line = ""
    if settings.llm_provider == "openai_compatible" and settings.llm_base_url:
        base_line = f"Base URL    : [cyan]{settings.llm_base_url}[/cyan]\n"

    console.print(
        Panel.fit(
            "[bold green]thelab-langchain[/bold green]\n\n"
            f"LLM Provider : [cyan]{settings.llm_provider}[/cyan]  (model: [bold]{settings.llm_model}[/bold])\n"
            f"{base_line}"
            f"Memory       : [magenta]Supermemory[/magenta]  (container: [bold]{settings.default_user_id}[/bold])\n\n"
            "Type your message and press Enter.\n"
            "Special commands: [bold]/profile[/bold], [bold]/clear[/bold], [bold]/user <id>[/bold], [bold]/quit[/bold]",
            title="Memory-Aware Chat Ready",
            border_style="green",
        )
    )


@app.command()
def chat(
    user: Annotated[
        str | None,
        typer.Option("--user", "-u", help="User/container ID for Supermemory isolation"),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Override LLM model name"),
    ] = None,
) -> None:
    """Start an interactive memory-aware chat session."""
    if model:
        settings.llm_model = model  # type: ignore[attr-defined]

    if settings.llm_provider == "openai_compatible" and not settings.llm_base_url:
        console.print(
            "[yellow]Warning:[/yellow] LLM_PROVIDER=openai_compatible but no LLM_BASE_URL set.\n"
            "Set LLM_BASE_URL (e.g. http://localhost:8000/v1 for local NIM on DGX Spark)."
        )

    user_id = user or settings.default_user_id
    agent = MemoryChat(user_id=user_id)

    _print_welcome()

    while True:
        try:
            message = Prompt.ask("\n[bold blue]You[/bold blue]", console=console).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if not message:
            continue

        # Slash commands
        if message.startswith("/"):
            cmd = message.lower().split()
            if cmd[0] in ("/quit", "/exit", "/q"):
                console.print("[green]Session ended. Memories remain in Supermemory.[/green]")
                break
            if cmd[0] == "/profile":
                agent.show_profile()
                continue
            if cmd[0] == "/clear":
                agent.clear_session()
                continue
            if cmd[0] == "/user" and len(cmd) > 1:
                new_user = cmd[1]
                agent = MemoryChat(user_id=new_user)
                console.print(f"[green]Switched to user container:[/green] [bold]{new_user}[/bold]")
                continue
            if cmd[0] == "/help":
                console.print(
                    "Commands: /profile, /clear, /user <id>, /quit\n"
                    "Everything else is sent to the LLM with memory context."
                )
                continue

            console.print("[red]Unknown command. Try /help[/red]")
            continue

        # Normal chat turn
        try:
            reply = agent.chat(message)
            console.print("\n[bold magenta]Assistant[/bold magenta]")
            console.print(Markdown(reply))
        except Exception as exc:
            console.print(f"[red]Error during chat:[/red] {exc}")
            if Confirm.ask("Continue session?", default=True):
                continue
            break


@app.command()
def profile(user: str = typer.Argument(None, help="User ID to inspect")) -> None:
    """Print the current Supermemory profile for a user (debug)."""
    user_id = user or settings.default_user_id
    agent = MemoryChat(user_id=user_id)
    agent.show_profile()


@app.command()
def env() -> None:
    """Show resolved configuration (secrets redacted)."""
    base_url = settings.llm_base_url or "(not set - using provider default)"
    effective_key = "✓ set" if settings.effective_llm_api_key else "✗ missing"

    console.print(Panel.fit(
        f"LLM Provider : {settings.llm_provider}\n"
        f"LLM Model    : {settings.llm_model}\n"
        f"LLM Base URL : {base_url}\n"
        f"Default User : {settings.default_user_id}\n"
        f"XAI key      : {'✓ set' if settings.xai_api_key else '✗ missing'}\n"
        f"Anthropic key: {'✓ set' if settings.anthropic_api_key else '✗ missing'}\n"
        f"OpenAI-comp. : {effective_key}\n"
        f"Supermemory  : {'✓ set' if settings.supermemory_api_key else '✗ missing'}",
        title="Current Settings",
    ))


@app.command()
def voice(
    user: Annotated[str | None, typer.Option("--user", "-u", help="User/container ID for memory")] = None,
    thread: Annotated[str | None, typer.Option("--thread", "-t", help="Session thread ID")] = None,
    riva_uri: Annotated[str | None, typer.Option("--riva", help="Riva server address (host:port)")] = None,
) -> None:
    """
    Start a voice conversation using local NVIDIA NeMo/Riva (ASR + TTS).

    This is the voice interface to the LangGraph + Supermemory brain.
    Requires a running Riva server (typically on DGX Spark).
    """
    user_id = user or settings.default_user_id
    thread_id = thread or "voice-session"

    console.print(
        Panel.fit(
            f"[bold green]Voice Mode[/bold green]\n\n"
            f"User    : [cyan]{user_id}[/cyan]\n"
            f"Thread  : [cyan]{thread_id}[/cyan]\n"
            f"Riva    : [magenta]{riva_uri or 'localhost:50051'}[/magenta]\n\n"
            "Speak naturally. Press Ctrl+C to exit.",
            title="thelab-chat voice",
            border_style="green",
        )
    )

    try:
        # Lazy import so the rest of the CLI works without audio runtime deps
        from .voice import VoiceOrchestrator
    except Exception as exc:
        console.print(
            "[red]Voice dependencies are not available.[/red]\n"
            "Install with: pip install 'thelab-langchain[voice]'\n"
            "(requires libportaudio2 and a working microphone/speakers for full functionality)"
        )
        raise typer.Exit(1) from exc

    try:
        orchestrator = VoiceOrchestrator(
            user_id=user_id,
            thread_id=thread_id,
            riva_uri=riva_uri,
        )
        import asyncio
        asyncio.run(orchestrator.start_voice_session())
    except KeyboardInterrupt:
        console.print("\n[yellow]Voice session ended.[/yellow]")
    except Exception as exc:
        console.print(f"[red]Voice session failed:[/red] {exc}")


if __name__ == "__main__":
    app()
