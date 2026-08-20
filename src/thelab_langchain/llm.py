"""
LLM factory for the TheLab agent.

Supports:
- xai (Grok via langchain-xai)
- anthropic (Claude via langchain-anthropic)
- openai_compatible (Nemotron NIM, vLLM, Ollama, etc. via langchain-openai)

This is the single place that knows how to construct the right chat model
based on environment configuration.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .config import settings


def get_chat_model() -> BaseChatModel:
    """
    Returns the configured chat model based on LLM_PROVIDER.
    """
    if settings.llm_provider == "xai":
        from langchain_xai import ChatXAI

        return ChatXAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.xai_api_key.get_secret_value() if settings.xai_api_key else None,
        )

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            api_key=settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None,
        )

    if settings.llm_provider == "openai_compatible":
        from langchain_openai import ChatOpenAI

        # For local Nemotron / vLLM / NIMs, the key is often "dummy"
        api_key = (
            settings.openai_compatible_api_key.get_secret_value()
            if settings.openai_compatible_api_key
            else "dummy"
        )

        return ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            base_url=settings.llm_base_url,
            api_key=api_key,
        )

    raise ValueError(f"Unsupported llm_provider: {settings.llm_provider}")
