"""Deterministic Mock LLM Provider for unit, integration, and evaluation testing."""
from typing import Any
from backend.app.agent.models import AgentDecision


class MockLLMProvider:
    """
    Deterministic provider that returns predefined turns or scripted reactions.
    Enables zero-cost, 100% reproducible agent testing.
    """

    def __init__(self, scripted_decisions: list[AgentDecision] | None = None) -> None:
        self.scripted_decisions = list(scripted_decisions or [])
        self.call_count = 0
        self.history: list[dict[str, Any]] = []

    def set_script(self, decisions: list[AgentDecision]) -> None:
        self.scripted_decisions = list(decisions)
        self.call_count = 0

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        self.history.append({"messages": messages, "tools": tools})

        if self.call_count < len(self.scripted_decisions):
            decision = self.scripted_decisions[self.call_count]
            self.call_count += 1
            return decision

        # Fallback if decisions exhausted: declare completion
        return AgentDecision(
            investigation="All prescribed mock steps concluded.",
            hypothesis="Mock execution finished.",
            action_plan="Terminate mock loop.",
            tool_calls=[],
            indicates_completion=True,
            root_cause_report="Mock execution completed successfully.",
        )
