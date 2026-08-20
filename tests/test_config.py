"""Tests for Settings.validate_keys.

Pure configuration logic. `_env_file=None` keeps each test hermetic (the working
tree's real .env is ignored); provider selection and keys are driven entirely by
monkeypatched environment variables.
"""

from __future__ import annotations

import pytest

from thelab_langchain.config import Settings


def _settings() -> Settings:
    return Settings(_env_file=None)


def test_validate_keys_ok_for_xai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key")
    monkeypatch.setenv("SUPERMEMORY_API_KEY", "sm-test-key")

    _settings().validate_keys()  # should not raise


def test_validate_keys_missing_xai_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("SUPERMEMORY_API_KEY", "sm-test-key")
    monkeypatch.delenv("XAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="XAI_API_KEY"):
        _settings().validate_keys()


def test_validate_keys_missing_anthropic_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("SUPERMEMORY_API_KEY", "sm-test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        _settings().validate_keys()


def test_validate_keys_openai_compatible_requires_base_url(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("SUPERMEMORY_API_KEY", "sm-test-key")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="LLM_BASE_URL"):
        _settings().validate_keys()


def test_validate_keys_missing_supermemory_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key")
    monkeypatch.delenv("SUPERMEMORY_API_KEY", raising=False)

    with pytest.raises(ValueError, match="SUPERMEMORY_API_KEY"):
        _settings().validate_keys()
