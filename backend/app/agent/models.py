"""Data models and enums for Agent State, Status, and Telemetry."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Explicit lifecycle statuses for DevAgent."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    RECONNAISSING = "RECONNAISSING"
    INVESTIGATING = "INVESTIGATING"
    PATCHING = "PATCHING"
    VERIFYING = "VERIFYING"
    CORRECTING = "CORRECTING"
    COMPLETED = "COMPLETED"
    COMPLETED_WITHOUT_VERIFICATION = "COMPLETED_WITHOUT_VERIFICATION"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class ToolCallRecord(BaseModel):
    """Log record of an individual tool invocation."""

    id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VerificationRecord(BaseModel):
    """Log record of a test suite execution."""

    runner: str
    args: list[str]
    exit_code: int
    passed: bool
    stdout: str
    stderr: str
    duration_seconds: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PatchRecord(BaseModel):
    """Log record of an atomic patch applied to a file."""

    file_path: str
    diff: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentDecision(BaseModel):
    """Structured decision returned by an LLM provider."""

    investigation: str | None = Field(default=None, description="Observation or findings from previous step")
    hypothesis: str | None = Field(default=None, description="Current working theory of the bug")
    action_plan: str | None = Field(default=None, description="Planned action for this step")
    tool_calls: list[dict[str, Any]] = Field(default_factory=list, description="Requested tool invocations")
    indicates_completion: bool = Field(default=False, description="Whether the LLM claims the issue is solved")
    root_cause_report: str | None = Field(default=None, description="Structured root cause report upon completion")
