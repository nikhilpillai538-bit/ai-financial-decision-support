"""
Provider-independent LLM service abstraction for Phase 9.

Supports OpenAI, Anthropic, Mock (testing/offline), and Unconfigured providers.
Uses httpx for resilient asynchronous HTTP communication with zero vendor SDK lock-in.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, List, Optional

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import httpx

from app.ai.config import LLMSettings, get_llm_settings, mask_api_key

logger = logging.getLogger("uvicorn.error")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMProviderError(LLMError):
    """Raised on provider server errors (5xx) or unparseable responses."""
    pass


class LLMNotConfiguredError(LLMProviderError):
    """Raised when an LLM operation is requested without valid provider credentials."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when the LLM provider call exceeds the configured timeout."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when the LLM provider returns a 429 rate limit response."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when the LLM provider rejects the API key (401/403)."""
    pass


# ---------------------------------------------------------------------------
# Message & Response Models
# ---------------------------------------------------------------------------

@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    finish_reason: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    raw_payload: Optional[Dict[str, Any]] = field(default=None, repr=False)

    @property
    def provider(self) -> str:
        return "mock" if "mock" in self.model else "external"

    @property
    def usage(self) -> Dict[str, int]:
        p = self.prompt_tokens or 0
        c = self.completion_tokens or 0
        return {"prompt_tokens": p, "completion_tokens": c, "total_tokens": p + c}


# ---------------------------------------------------------------------------
# Abstract Provider Interface
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract interface for LLM provider implementations."""

    @property
    def name(self) -> str:
        return "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is configured with credentials."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM given message history."""
        pass

    async def generate_chat_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Convenience helper to generate response with prepended system prompt."""
        full_messages: List[LLMMessage] = []
        if system_prompt:
            full_messages.append(LLMMessage(role="system", content=system_prompt))
        full_messages.extend(messages)
        return await self.generate(full_messages, temperature=temperature)


# ---------------------------------------------------------------------------
# Unconfigured Provider
# ---------------------------------------------------------------------------

class UnconfiguredProvider(BaseLLMProvider):
    """Fallback provider when no valid credentials or mock provider is configured."""

    def __init__(self, message: str = "LLM provider is not configured. Please set LLM_PROVIDER and LLM_API_KEY."):
        self.message = message

    @property
    def name(self) -> str:
        return "unconfigured"

    def is_configured(self) -> bool:
        return False

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        raise LLMNotConfiguredError(self.message)


# ---------------------------------------------------------------------------
# OpenAI Provider
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI Chat Completions API."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.api_key = settings.api_key
        self.model = settings.get_effective_model()
        if not settings.api_base and settings.provider == "groq":
            self.base_url = "https://api.groq.com/openai/v1"
        else:
            self.base_url = (settings.api_base or "https://api.openai.com/v1").rstrip("/")
        self.timeout = httpx.Timeout(settings.timeout_seconds)

    @property
    def name(self) -> str:
        return self.settings.provider

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        if not self.is_configured():
            raise LLMNotConfiguredError("LLM API key is missing. Set LLM_API_KEY in environment.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        # Build list of candidate models for automatic failover (especially on Groq)
        candidate_models = [self.model]
        if self.settings.provider == "groq":
            for fallback_m in ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"]:
                if fallback_m not in candidate_models:
                    candidate_models.append(fallback_m)

        last_error: Optional[Exception] = None

        for model_to_use in candidate_models:
            body: Dict[str, Any] = {
                "model": model_to_use,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": self.settings.max_output_tokens,
            }
            if response_format == "json":
                body["response_format"] = {"type": "json_object"}

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(url, headers=headers, json=body)
            except httpx.TimeoutException as exc:
                last_error = LLMTimeoutError(f"LLM request timed out after {self.settings.timeout_seconds}s for model {model_to_use}.")
                logger.warning("LLM timeout for model %s: %s", model_to_use, exc)
                continue
            except httpx.RequestError as exc:
                last_error = LLMProviderError(f"LLM network error for model {model_to_use}: {type(exc).__name__}")
                logger.warning("LLM network error for model %s: %s", model_to_use, exc)
                continue

            if res.status_code == 401 or res.status_code == 403:
                raise LLMAuthenticationError(f"LLM authentication failed: invalid or expired API key ({res.text[:120]}).")
            if res.status_code == 429:
                last_error = LLMRateLimitError(f"Rate limit exceeded for model {model_to_use}.")
                logger.warning("Rate limit on model %s, trying next candidate...", model_to_use)
                continue
            if res.status_code >= 500:
                last_error = LLMProviderError(f"Service error HTTP {res.status_code} for model {model_to_use}.")
                logger.warning("Provider 5xx error on model %s, trying next candidate...", model_to_use)
                continue
            if res.status_code != 200:
                last_error = LLMProviderError(f"Unexpected status HTTP {res.status_code} for model {model_to_use}: {res.text[:200]}")
                logger.warning("Unexpected status on model %s: %s", model_to_use, res.text[:200])
                continue

            try:
                payload = res.json()
                choice = payload["choices"][0]
                content = choice["message"]["content"]
                usage = payload.get("usage", {})
                return LLMResponse(
                    content=content,
                    model=payload.get("model", model_to_use),
                    finish_reason=choice.get("finish_reason"),
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    raw_payload=payload,
                )
            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                last_error = LLMProviderError(f"Malformed response payload from model {model_to_use}: {exc}")
                logger.warning("Malformed payload from model %s: %s", model_to_use, exc)
                continue

        if last_error:
            raise last_error
        raise LLMProviderError("All candidate LLM models failed to produce a valid response.")



# ---------------------------------------------------------------------------
# Anthropic Provider
# ---------------------------------------------------------------------------

class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic Messages API."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.api_key = settings.api_key
        self.model = settings.get_effective_model()
        self.base_url = (settings.api_base or "https://api.anthropic.com/v1").rstrip("/")
        self.timeout = httpx.Timeout(settings.timeout_seconds)

    @property
    def name(self) -> str:
        return "anthropic"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        if not self.is_configured():
            raise LLMNotConfiguredError("Anthropic API key is missing. Set LLM_API_KEY in environment.")

        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Separate system messages from user/assistant turns
        system_text = "\n\n".join(m.content for m in messages if m.role == "system")
        conversation_turns = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in {"user", "assistant"}
        ]

        body: Dict[str, Any] = {
            "model": self.model,
            "messages": conversation_turns,
            "max_tokens": self.settings.max_output_tokens,
            "temperature": temperature,
        }
        if system_text:
            body["system"] = system_text

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=headers, json=body)
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(f"Anthropic request timed out after {self.settings.timeout_seconds}s.") from exc
        except httpx.RequestError as exc:
            raise LLMProviderError(f"Anthropic network error: {type(exc).__name__}") from exc

        if res.status_code == 401 or res.status_code == 403:
            raise LLMAuthenticationError("Anthropic authentication failed: invalid or expired API key.")
        if res.status_code == 429:
            raise LLMRateLimitError("Anthropic rate limit exceeded.")
        if res.status_code >= 500:
            raise LLMProviderError(f"Anthropic service error (HTTP {res.status_code}).")
        if res.status_code != 200:
            raise LLMProviderError(f"Anthropic returned unexpected status HTTP {res.status_code}: {res.text[:200]}")

        try:
            payload = res.json()
            content_block = payload["content"][0]["text"]
            usage = payload.get("usage", {})
            return LLMResponse(
                content=content_block,
                model=payload.get("model", self.model),
                finish_reason=payload.get("stop_reason"),
                prompt_tokens=usage.get("input_tokens"),
                completion_tokens=usage.get("output_tokens"),
                raw_payload=payload,
            )
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMProviderError(f"Malformed response payload from Anthropic: {exc}") from exc


# ---------------------------------------------------------------------------
# Mock LLM Provider (Testing & Offline Development)
# ---------------------------------------------------------------------------

class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for automated unit tests and offline testing."""

    def __init__(self, canned_response: Optional[str] = None):
        self.canned_response = canned_response
        self.call_count = 0
        self.last_messages: List[LLMMessage] = []
        self.should_fail_with: Optional[Exception] = None

    @property
    def name(self) -> str:
        return "mock"

    def is_configured(self) -> bool:
        return True

    def set_canned_response(self, text: str):
        self.canned_response = text

    def set_error(self, exc: Optional[Exception]):
        self.should_fail_with = exc

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        response_format: Optional[str] = None,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages

        if self.should_fail_with:
            raise self.should_fail_with

        if self.canned_response is not None:
            text = self.canned_response
        else:
            # Dynamically determine domains from user query for mock response
            user_content = " ".join(m.content.lower() for m in messages if m.role == "user")
            detected_domains = []
            if any(k in user_content for k in ["spend", "expense", "budget", "saving", "cash"]):
                detected_domains.append("spending_and_cash_flow")
            if any(k in user_content for k in ["emergency", "buffer", "safety"]):
                detected_domains.append("emergency_fund")
            if any(k in user_content for k in ["goal", "target", "retire", "sip"]):
                detected_domains.append("investment_goals")
            if any(k in user_content for k in ["portfolio", "asset", "stock", "holding", "sharpe", "risk"]):
                detected_domains.append("portfolio_risk_and_allocation")
            if any(k in user_content for k in ["drift", "rebalance", "deviation"]):
                detected_domains.append("rebalancing_and_drift")
            if not detected_domains:
                detected_domains = ["spending_and_cash_flow", "emergency_fund", "portfolio_risk_and_allocation"]

            text = json.dumps({
                "answer": (
                    "Based on your verified financial records, your portfolio holds a disciplined asset distribution. "
                    "Your emergency fund is active and your spending trends remain within reasonable bounds."
                ),
                "cited_domains": detected_domains,
                "key_metrics_cited": {},
                "limitations_or_missing_data": [],
                "suggested_follow_ups": [
                    "Would you like to analyze a hypothetical SIP contribution increase?",
                    "Should we review your asset allocation drift against target weights?"
                ],
                "disclaimer": "Educational and decision-support guidance only. Not financial, tax, or legal advice."
            })

        return LLMResponse(
            content=text,
            model="mock-financial-assistant-v1",
            finish_reason="stop",
            prompt_tokens=150,
            completion_tokens=85,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_llm_provider(settings: Optional[LLMSettings] = None) -> BaseLLMProvider:
    """Create and return configured LLM provider adapter."""
    s = settings or get_llm_settings()
    provider_name = s.provider.lower()

    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name in {"openai", "groq"}:
        if not s.api_key:
            return UnconfiguredProvider(f"{provider_name.capitalize()} provider selected but API key is not configured. Set LLM_API_KEY or GROQ_API_KEY.")
        return OpenAIProvider(s)
    elif provider_name == "anthropic":
        if not s.api_key:
            return UnconfiguredProvider("Anthropic provider selected but LLM_API_KEY is not configured.")
        return AnthropicProvider(s)
    elif provider_name in {"none", ""}:
        return UnconfiguredProvider("No LLM provider configured. Set LLM_PROVIDER to 'openai', 'anthropic', or 'mock'.")
    else:
        return UnconfiguredProvider(f"Unknown LLM provider '{s.provider}'. Supported: 'openai', 'anthropic', 'mock'.")
