"""AgentState representing the complete runtime context of a DevAgent session."""
import time
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from backend.app.agent.events import AgentEvent
from backend.app.agent.models import (
    AgentStatus,
    PatchRecord,
    ToolCallRecord,
    VerificationRecord,
)


class AgentState(BaseModel):
    """Encapsulates all mutable state for an individual agent session."""

    session_id: str
    issue: str
    workspace: Path
    verification_instruction: str | None = None

    status: AgentStatus = AgentStatus.CREATED

    iteration: int = 0
    max_iterations: int = 8

    tool_calls_count: int = 0
    max_tool_calls: int = 20

    verification_attempts: int = 0
    max_verification_attempts: int = 5

    messages: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    events: list[AgentEvent] = Field(default_factory=list)

    files_changed: list[str] = Field(default_factory=list)
    patches: list[PatchRecord] = Field(default_factory=list)
    verification_runs: list[VerificationRecord] = Field(default_factory=list)

    current_hypothesis: str | None = None
    root_cause: str | None = None
    final_diff: str | None = None
    error: str | None = None

    cancel_requested: bool = False
    started_at: float = Field(default_factory=time.time)
    completed_at: float | None = None

    def record_patch(self, file_path: str, diff: str) -> None:
        """Track file modifications and composite diffs."""
        if file_path not in self.files_changed:
            self.files_changed.append(file_path)
        self.patches.append(PatchRecord(file_path=file_path, diff=diff))

        # Recompute final unified diff
        all_diffs = [p.diff for p in self.patches]
        self.final_diff = "\n".join(all_diffs)

    def record_verification(self, record: VerificationRecord) -> None:
        """Track test executions and increment attempts count."""
        self.verification_attempts += 1
        self.verification_runs.append(record)

    def record_tool_call(self, record: ToolCallRecord) -> None:
        """Track tool invocation count and history."""
        self.tool_calls_count += 1
        self.tool_calls.append(record)

    def has_passed_verification(self) -> bool:
        """Check if at least one verification attempt succeeded."""
        return any(v.passed for v in self.verification_runs)

    def last_verification_passed(self) -> bool:
        """Check if the most recent verification attempt passed."""
        if not self.verification_runs:
            return False
        return self.verification_runs[-1].passed
