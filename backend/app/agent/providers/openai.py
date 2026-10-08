"""OpenAI-compatible LLM provider with structured tool calling."""
import json
import os
from typing import Any
from backend.app.agent.models import AgentDecision
from backend.app.agent.prompts import build_system_prompt
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger("provider.openai")


class OpenAIProvider:
    """OpenAI-compatible provider supporting GPT-4o, Claude via proxy, or local models."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or get_settings().openai_api_key
        self.model_name = model or "gpt-4o"

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY.")

        system_msg = {
            "role": "system",
            "content": build_system_prompt() + (
                "\nRespond ONLY with a JSON object containing keys: "
                "'investigation', 'hypothesis', 'action_plan', 'tool_calls', 'indicates_completion', 'root_cause_report'."
            ),
        }

        openai_messages = [system_msg]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ("user", "assistant", "system"):
                openai_messages.append({"role": role, "content": str(content)})
            elif role == "tool":
                openai_messages.append({"role": "user", "content": f"TOOL RESULT ({m.get('name')}): {content}"})

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or "{}"
            data = json.loads(raw_text)
            return AgentDecision.model_validate(data)
        except Exception as e:
            logger.error(f"OpenAI API completion error: {e}")
            raise
