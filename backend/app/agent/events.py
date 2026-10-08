"""Event models for DevAgent real-time observability and SSE streaming."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    SESSION_CREATED = "session.created"
    AGENT_STARTED = "agent.started"
    AGENT_STEP_STARTED = "agent.step.started"
    AGENT_TELEMETRY = "agent.telemetry"
    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    PATCH_CREATED = "patch.created"
    VERIFICATION_STARTED = "verification.started"
    VERIFICATION_COMPLETED = "verification.completed"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_CANCELLED = "agent.cancelled"


class AgentEvent(BaseModel):
    """Standardized event envelope emitted during agent execution."""

    type: EventType
    session_id: str
    step: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = Field(default_factory=dict)

    def to_sse_dict(self) -> dict[str, Any]:
        """Convert to Server-Sent Event data payload."""
        return {
            "event": self.type.value,
            "data": {
                "type": self.type.value,
                "session_id": self.session_id,
                "step": self.step,
                "timestamp": self.timestamp,
                "data": self.data,
            },
        }
