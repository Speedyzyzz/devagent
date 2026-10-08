"""Abstract protocol and base classes for LLM Providers."""
from typing import Any, Protocol
from backend.app.agent.models import AgentDecision


class LLMProvider(Protocol):
    """Protocol that all DevAgent LLM integrations must satisfy."""

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        """Generate the next agent step decision given conversation history and tools."""
        ...
