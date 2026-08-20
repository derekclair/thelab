"""Configuration for LLM and Supermemory clients."""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Supermemory (required at runtime, not at import)
    supermemory_api_key: SecretStr | None = Field(
        default=None, alias="SUPERMEMORY_API_KEY", description="Supermemory API key"
    )

    # LLM Provider selection
    llm_provider: Literal["xai", "anthropic", "openai_compatible"] = Field(
        default="xai", alias="LLM_PROVIDER"
    )

    # Model names
    llm_model: str = Field(
        default="grok-3",
        alias="LLM_MODEL",
        description="Model identifier (grok-3, grok-4, claude-3-7-sonnet-20250219, ...)",
    )

    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")

    # For local / Nemotron / any OpenAI-compatible endpoint
    llm_base_url: str | None = Field(
        default=None, alias="LLM_BASE_URL",
        description="Base URL for OpenAI-compatible endpoints (e.g. http://localhost:8000/v1 for local NIM on DGX Spark)"
    )

    # Demo defaults
    default_user_id: str = Field(default="demo-user", alias="DEFAULT_USER_ID")

    @property
    def xai_api_key(self) -> SecretStr | None:
        key = os.getenv("XAI_API_KEY")
        return SecretStr(key) if key else None

    @property
    def anthropic_api_key(self) -> SecretStr | None:
        key = os.getenv("ANTHROPIC_API_KEY")
        return SecretStr(key) if key else None

    @property
    def openai_compatible_api_key(self) -> SecretStr | None:
        """For local Nemotron / vLLM / any OpenAI-compatible server.
        Many local servers accept any key or 'dummy'.
        """
        key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or "dummy"
        return SecretStr(key)

    @property
    def effective_llm_api_key(self) -> SecretStr | None:
        if self.llm_provider == "xai":
            return self.xai_api_key
        if self.llm_provider == "anthropic":
            return self.anthropic_api_key
        if self.llm_provider == "openai_compatible":
            return self.openai_compatible_api_key
        return None

    def validate_keys(self) -> None:
        """Ensure the required API key for the chosen provider is present."""
        if self.llm_provider == "xai" and not self.xai_api_key:
            raise ValueError(
                "XAI_API_KEY is required when LLM_PROVIDER=xai. "
                "Get one at https://console.x.ai/"
            )
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic. "
                "Get one at https://console.anthropic.com/"
            )
        if self.llm_provider == "openai_compatible" and not self.llm_base_url:
            raise ValueError(
                "LLM_BASE_URL is required when LLM_PROVIDER=openai_compatible "
                "(e.g. http://nemotron:8000/v1 for local Nemotron NIM)."
            )
        if not self.supermemory_api_key:
            raise ValueError(
                "SUPERMEMORY_API_KEY is required. "
                "Get one at https://console.supermemory.ai/"
            )


settings = Settings()
