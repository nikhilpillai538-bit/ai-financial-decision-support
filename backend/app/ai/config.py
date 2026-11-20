"""
Configuration and settings for Phase 9 LLM integrations.

Supports OpenAI, Anthropic, Mock (testing/development), and Unconfigured providers.
Secrets are never logged or exposed in responses.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    """Runtime configuration for LLM provider."""

    provider: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "mock").strip().lower()
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: (os.getenv("LLM_API_KEY", "") or os.getenv("GROQ_API_KEY", "")).strip() or None
    )
    model: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "").strip()
    )
    timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))
    )
    max_output_tokens: int = Field(
        default_factory=lambda: int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1200"))
    )
    api_base: Optional[str] = Field(
        default_factory=lambda: os.getenv("LLM_API_BASE", "").strip() or None
    )

    @property
    def is_configured(self) -> bool:
        """Return True if a usable provider and API key (or mock) are present."""
        if self.provider == "mock":
            return True
        if self.provider in {"openai", "anthropic", "groq"} and self.api_key and len(self.api_key) > 5:
            return True
        return False

    def get_effective_model(self) -> str:
        """Return model name, applying sensible defaults per provider."""
        if self.model:
            return self.model
        if self.provider == "groq":
            return "openai/gpt-oss-120b"
        if self.provider == "openai":
            return "gpt-4o-mini"
        if self.provider == "anthropic":
            return "claude-3-5-haiku-latest"
        return "mock-financial-model"


def get_llm_settings() -> LLMSettings:
    """Load settings dynamically from current environment variables."""
    return LLMSettings()


def mask_api_key(key: Optional[str]) -> str:
    """Safely mask an API key for logs or status checks without leaking secrets."""
    if not key or len(key) < 8:
        return "[NOT CONFIGURED]"
    return f"{key[:4]}...{key[-4:]}"
