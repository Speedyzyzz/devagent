"""Google Gemini LLM provider integration with native function calling."""
import json
import os
from typing import Any
from backend.app.agent.models import AgentDecision
from backend.app.agent.prompts import build_system_prompt
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger("provider.gemini")


class GeminiProvider:
    """Gemini provider using Google GenAI SDK for tool calling and reasoning."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or get_settings().gemini_api_key
        self.model_name = model or "gemini-2.5-flash"

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AgentDecision:
        if not self.client:
            raise RuntimeError("Gemini Client not initialized. Set GEMINI_API_KEY.")

        # Prepare messages and system instruction
        prompt_lines = [build_system_prompt(), "\nCONVERSATION HISTORY:"]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_lines.append(f"[{role.upper()}]: {content}")

        prompt_lines.append(
            "\nNow, choose the next action. Output a valid JSON object matching the following structure:\n"
            "{\n"
            '  "investigation": "...",\n'
            '  "hypothesis": "...",\n'
            '  "action_plan": "...",\n'
            '  "tool_calls": [{"name": "tool_name", "arguments": {...}}],\n'
            '  "indicates_completion": false,\n'
            '  "root_cause_report": null\n'
            "}\n"
            "If the bug is verified and solved, set indicates_completion=true and provide root_cause_report."
        )

        full_prompt = "\n".join(prompt_lines)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(response.text)
            return AgentDecision.model_validate(data)
        except Exception as e:
            logger.error(f"Gemini API completion error: {e}")
            raise
