"""Tests for get_chat_model provider routing.

Fake provider modules are injected into sys.modules so that no real LangChain
provider package (langchain-xai / langchain-anthropic / langchain-openai) needs
to be installed and no client ever makes a network call.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from thelab_langchain import config, llm


def _fake_provider(module_name: str, class_name: str):
    """Register a fake provider module and return (module, fake_class)."""
    module = types.ModuleType(module_name)
    fake_class = MagicMock(name=class_name)
    setattr(module, class_name, fake_class)
    return module, fake_class


def test_get_chat_model_routes_to_xai(monkeypatch):
    module, chat_xai = _fake_provider("langchain_xai", "ChatXAI")
    monkeypatch.setitem(sys.modules, "langchain_xai", module)
    monkeypatch.setattr(config.settings, "llm_provider", "xai")

    result = llm.get_chat_model()

    assert result is chat_xai.return_value
    chat_xai.assert_called_once()
    assert chat_xai.call_args.kwargs["model"] == config.settings.llm_model


def test_get_chat_model_routes_to_anthropic(monkeypatch):
    module, chat_anthropic = _fake_provider("langchain_anthropic", "ChatAnthropic")
    monkeypatch.setitem(sys.modules, "langchain_anthropic", module)
    monkeypatch.setattr(config.settings, "llm_provider", "anthropic")

    result = llm.get_chat_model()

    assert result is chat_anthropic.return_value
    chat_anthropic.assert_called_once()


def test_get_chat_model_routes_to_openai_compatible(monkeypatch):
    module, chat_openai = _fake_provider("langchain_openai", "ChatOpenAI")
    monkeypatch.setitem(sys.modules, "langchain_openai", module)
    monkeypatch.setattr(config.settings, "llm_provider", "openai_compatible")
    monkeypatch.setattr(config.settings, "llm_base_url", "http://localhost:8000/v1")

    result = llm.get_chat_model()

    assert result is chat_openai.return_value
    kwargs = chat_openai.call_args.kwargs
    assert kwargs["base_url"] == "http://localhost:8000/v1"
    # Local OpenAI-compatible servers accept any key; a non-empty fallback is used.
    assert kwargs["api_key"]


def test_get_chat_model_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(config.settings, "llm_provider", "does-not-exist")
    with pytest.raises(ValueError, match="Unsupported llm_provider"):
        llm.get_chat_model()
