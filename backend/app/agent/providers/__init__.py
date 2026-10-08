"""Providers module and factory function."""
from backend.app.agent.providers.base import LLMProvider
from backend.app.agent.providers.gemini import GeminiProvider
from backend.app.agent.providers.mock import MockLLMProvider
from backend.app.agent.providers.openai import OpenAIProvider
from backend.app.core.config import get_settings


def get_llm_provider(provider_type: str | None = None, model: str | None = None) -> LLMProvider:
    """Retrieve LLM provider instance based on type."""
    settings = get_settings()
    active_type = (provider_type or settings.llm_provider).lower()
    active_model = model or settings.llm_model

    if active_type == "gemini":
        return GeminiProvider(model=active_model)
    elif active_type == "openai":
        return OpenAIProvider(model=active_model)
    else:
        return MockLLMProvider()


__all__ = [
    "LLMProvider",
    "MockLLMProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "get_llm_provider",
]
