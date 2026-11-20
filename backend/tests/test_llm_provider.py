"""
Unit tests for Phase 9 LLM Provider Abstraction and Configuration.
"""

import asyncio
import json
import os
import pytest

from app.ai.config import LLMSettings, get_llm_settings, mask_api_key
from app.ai.provider import (
    AnthropicProvider,
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMMessage,
    LLMNotConfiguredError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponse,
    LLMTimeoutError,
    MockLLMProvider,
    OpenAIProvider,
    UnconfiguredProvider,
    get_llm_provider,
)


class TestLLMConfig:
    def test_default_settings(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_MODEL", raising=False)

        settings = LLMSettings()
        assert settings.provider == "mock"
        assert settings.api_key is None
        assert settings.is_configured is True
        assert settings.timeout_seconds == 30.0
        assert settings.max_output_tokens == 1200

    def test_custom_env_settings(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("LLM_API_KEY", "sk-proj-test123456789")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")

        settings = get_llm_settings()
        assert settings.provider == "openai"
        assert settings.api_key == "sk-proj-test123456789"
        assert settings.model == "gpt-4o-mini"
        assert settings.timeout_seconds == 45.0
        assert settings.is_configured is True

    def test_mask_api_key(self):
        assert mask_api_key(None) == "[NOT CONFIGURED]"
        assert mask_api_key("") == "[NOT CONFIGURED]"
        assert mask_api_key("short") == "[NOT CONFIGURED]"
        masked = mask_api_key("sk-proj-1234567890abcdef")
        assert masked.startswith("sk-p")
        assert masked.endswith("cdef")
        assert "1234567890" not in masked


class TestMockLLMProvider:
    def test_mock_provider_spending_response(self):
        provider = MockLLMProvider()
        messages = [
            LLMMessage(role="user", content="What did I spend on groceries this month?")
        ]
        resp = asyncio.run(provider.generate_chat_response(
            messages=messages,
            system_prompt="System prompt with context",
        ))
        assert isinstance(resp, LLMResponse)
        assert resp.provider == "mock"
        assert "mock" in resp.model
        assert resp.usage["total_tokens"] > 0

        parsed = json.loads(resp.content)
        assert "answer" in parsed
        assert "cited_domains" in parsed
        assert "spending_and_cash_flow" in parsed["cited_domains"]
        assert "disclaimer" in parsed

    def test_mock_provider_emergency_fund_response(self):
        provider = MockLLMProvider()
        messages = [
            LLMMessage(role="user", content="How is my emergency fund buffer?")
        ]
        resp = asyncio.run(provider.generate_chat_response(messages=messages))
        parsed = json.loads(resp.content)
        assert "emergency_fund" in parsed["cited_domains"]

    def test_mock_provider_rebalance_response(self):
        provider = MockLLMProvider()
        messages = [
            LLMMessage(role="user", content="Does my portfolio have any drift to rebalance?")
        ]
        resp = asyncio.run(provider.generate_chat_response(messages=messages))
        parsed = json.loads(resp.content)
        assert "rebalancing_and_drift" in parsed["cited_domains"]

    def test_mock_provider_goals_response(self):
        provider = MockLLMProvider()
        messages = [
            LLMMessage(role="user", content="Are my investment goals on track?")
        ]
        resp = asyncio.run(provider.generate_chat_response(messages=messages))
        parsed = json.loads(resp.content)
        assert "investment_goals" in parsed["cited_domains"]


class TestUnconfiguredProvider:
    def test_unconfigured_provider_graceful_response(self):
        provider = UnconfiguredProvider()
        messages = [
            LLMMessage(role="user", content="Hello, can you help me?")
        ]
        with pytest.raises(LLMNotConfiguredError):
            asyncio.run(provider.generate(messages=messages))


class TestProviderExceptions:
    def test_custom_exception_hierarchy(self):
        assert issubclass(LLMTimeoutError, LLMProviderError)
        assert issubclass(LLMRateLimitError, LLMProviderError)
        assert issubclass(LLMAuthenticationError, LLMProviderError)
        assert issubclass(LLMNotConfiguredError, LLMProviderError)


class TestProviderFactory:
    def test_get_llm_provider_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        provider = get_llm_provider()
        assert isinstance(provider, MockLLMProvider)

    def test_get_llm_provider_unconfigured(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        provider = get_llm_provider()
        assert isinstance(provider, UnconfiguredProvider)
