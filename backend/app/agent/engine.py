"""Core Agent Engine running the autonomous debugging execution loop."""
import asyncio
import time
from typing import Any, Callable, Coroutine
from backend.app.agent.events import AgentEvent, EventType
from backend.app.agent.models import (
    AgentDecision,
    AgentStatus,
    ToolCallRecord,
    VerificationRecord,
)
from backend.app.agent.prompts import build_context_prompt, build_system_prompt
from backend.app.agent.providers.base import LLMProvider
from backend.app.agent.state import AgentState
from backend.app.agent.tools import ToolRegistry, create_default_registry
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger("agent.engine")

EventCallback = Callable[[AgentEvent], Coroutine[Any, Any, None]]


class AgentEngine:
    """Orchestrates the policy-constrained agent execution loop."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry | None = None,
        event_callback: EventCallback | None = None,
    ) -> None:
        self.llm = llm_provider
        self.tools = tool_registry or create_default_registry()
        self.event_callback = event_callback
        self.settings = get_settings()

    async def emit_event(self, state: AgentState, event_type: EventType, data: dict[str, Any]) -> AgentEvent:
        event = AgentEvent(
            type=event_type,
            session_id=state.session_id,
            step=state.iteration,
            data=data,
        )
        state.events.append(event)
        if self.event_callback:
            try:
                await self.event_callback(event)
            except Exception as e:
                logger.warning(f"Error in event callback: {e}")
        return event

    async def run(self, state: AgentState) -> AgentState:
        """Execute the autonomous loop until resolution, budget limit, or cancellation."""
        state.status = AgentStatus.INITIALIZING
        state.started_at = time.time()
        await self.emit_event(state, EventType.AGENT_STARTED, {
            "session_id": state.session_id,
            "issue": state.issue,
            "workspace": str(state.workspace),
        })

        # Prime conversation history with system rules and issue context
        state.messages.append({"role": "system", "content": build_system_prompt()})
        state.messages.append({
            "role": "user",
            "content": build_context_prompt(state.issue, state.verification_instruction),
        })

        tool_definitions = self.tools.get_definitions()

        while state.iteration < state.max_iterations:
            # 1. Budget & timeout enforcement
            if state.cancel_requested:
                state.status = AgentStatus.CANCELLED
                await self.emit_event(state, EventType.AGENT_CANCELLED, {"reason": "User cancelled session"})
                break

            elapsed = time.time() - state.started_at
            if elapsed > self.settings.max_runtime_seconds:
                state.status = AgentStatus.TIMEOUT
                state.error = f"Execution exceeded max runtime of {self.settings.max_runtime_seconds}s"
                await self.emit_event(state, EventType.AGENT_FAILED, {"reason": state.error})
                break

            if state.tool_calls_count >= state.max_tool_calls:
                state.status = AgentStatus.FAILED
                state.error = f"Exceeded maximum tool call budget ({state.max_tool_calls})"
                await self.emit_event(state, EventType.AGENT_FAILED, {"reason": state.error})
                break

            if state.verification_attempts >= state.max_verification_attempts:
                state.status = AgentStatus.FAILED
                state.error = f"Exceeded maximum verification attempts ({state.max_verification_attempts})"
                await self.emit_event(state, EventType.AGENT_FAILED, {"reason": state.error})
                break

            state.iteration += 1
            await self.emit_event(state, EventType.AGENT_STEP_STARTED, {"iteration": state.iteration})

            # 2. Query LLM provider for next decision
            try:
                decision: AgentDecision = await self.llm.complete(
                    messages=state.messages,
                    tools=tool_definitions,
                )
            except Exception as e:
                state.status = AgentStatus.FAILED
                state.error = f"LLM generation failed: {str(e)}"
                await self.emit_event(state, EventType.AGENT_FAILED, {"error": state.error})
                break

            # 3. Record telemetry
            if decision.hypothesis:
                state.current_hypothesis = decision.hypothesis
            if decision.investigation or decision.hypothesis or decision.action_plan:
                await self.emit_event(state, EventType.AGENT_TELEMETRY, {
                    "investigation": decision.investigation,
                    "hypothesis": decision.hypothesis,
                    "action_plan": decision.action_plan,
                })

            # 4. Handle tool execution requests
            if decision.tool_calls:
                for call_idx, tool_call in enumerate(decision.tool_calls):
                    if state.cancel_requested:
                        state.status = AgentStatus.CANCELLED
                        await self.emit_event(state, EventType.AGENT_CANCELLED, {"reason": "User cancelled session"})
                        return state

                    tool_name = tool_call.get("name")
                    arguments = tool_call.get("arguments", {})
                    call_id = f"call_{state.iteration}_{call_idx}"

                    # Update phase based on tool type
                    self._update_phase_for_tool(state, tool_name)

                    await self.emit_event(state, EventType.TOOL_CALLED, {
                        "tool": tool_name,
                        "arguments": arguments,
                        "call_id": call_id,
                    })

                    # Execute safely through registry
                    result = await self.tools.execute(
                        tool_name=tool_name,
                        arguments=arguments,
                        sandbox_root=state.workspace,
                    )

                    # Track tool call record
                    record = ToolCallRecord(
                        id=call_id,
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result.model_dump(),
                        success=result.success,
                    )
                    state.record_tool_call(record)

                    # Post-execution side effects
                    if tool_name == "apply_patch" and result.success and result.data:
                        patch_path = result.data.get("path", "")
                        diff_text = result.data.get("diff", "")
                        state.record_patch(patch_path, diff_text)
                        await self.emit_event(state, EventType.PATCH_CREATED, {
                            "file": patch_path,
                            "diff": diff_text,
                            "lines_added": result.data.get("lines_added", 0),
                            "lines_removed": result.data.get("lines_removed", 0),
                        })

                    elif tool_name == "execute_verification":
                        if result.success and result.data:
                            v_record = VerificationRecord(
                                runner=result.data.get("runner", "pytest"),
                                args=result.data.get("args", []),
                                exit_code=result.data.get("exit_code", 1),
                                passed=result.data.get("passed", False),
                                stdout=result.data.get("stdout", ""),
                                stderr=result.data.get("stderr", ""),
                                duration_seconds=result.data.get("duration_seconds", 0.0),
                            )
                            state.record_verification(v_record)
                            await self.emit_event(state, EventType.VERIFICATION_COMPLETED, {
                                "passed": v_record.passed,
                                "exit_code": v_record.exit_code,
                                "stdout": v_record.stdout[:1000],
                                "duration": v_record.duration_seconds,
                            })
                            if not v_record.passed:
                                state.status = AgentStatus.CORRECTING

                    if result.success:
                        await self.emit_event(state, EventType.TOOL_COMPLETED, {
                            "tool": tool_name,
                            "result": result.data,
                        })
                    else:
                        await self.emit_event(state, EventType.TOOL_FAILED, {
                            "tool": tool_name,
                            "error": result.error,
                        })

                    # Feed result back into conversation history
                    state.messages.append({
                        "role": "tool",
                        "name": tool_name,
                        "content": str(result.model_dump()),
                    })

            # 5. Evaluate completion claim
            if decision.indicates_completion:
                is_completed, reason = self._evaluate_completion(state)
                if is_completed:
                    state.status = AgentStatus.COMPLETED
                    state.root_cause = decision.root_cause_report or "Root cause resolved."
                    state.completed_at = time.time()
                    await self.emit_event(state, EventType.AGENT_COMPLETED, {
                        "iterations": state.iteration,
                        "files_changed": state.files_changed,
                        "final_diff": state.final_diff,
                        "root_cause": state.root_cause,
                    })
                    break
                else:
                    # Provide corrective feedback to the agent
                    state.messages.append({
                        "role": "user",
                        "content": f"SYSTEM: Cannot mark issue as resolved: {reason}. Continue investigating.",
                    })

        # Handle loop exhaustion without resolution
        if state.status not in (AgentStatus.COMPLETED, AgentStatus.CANCELLED, AgentStatus.TIMEOUT):
            state.status = AgentStatus.FAILED
            state.error = "Agent reached maximum iteration budget without a verified fix."
            await self.emit_event(state, EventType.AGENT_FAILED, {
                "reason": state.error,
                "iterations": state.iteration,
            })

        state.completed_at = time.time()
        return state

    def _update_phase_for_tool(self, state: AgentState, tool_name: str) -> None:
        if tool_name == "list_directory":
            state.status = AgentStatus.RECONNAISSING
        elif tool_name in ("search_code", "read_file_lines"):
            state.status = AgentStatus.INVESTIGATING
        elif tool_name == "apply_patch":
            state.status = AgentStatus.PATCHING
        elif tool_name == "execute_verification":
            state.status = AgentStatus.VERIFYING

    def _evaluate_completion(self, state: AgentState) -> tuple[bool, str]:
        """Engine-enforced completion policy (Section 25 & 26)."""
        if not state.files_changed:
            return False, "No files have been modified yet."

        if not state.verification_runs:
            return False, "Verification suite has not been executed."

        if not state.last_verification_passed():
            return False, "The latest verification run failed. You must fix the failures first."

        return True, "All requirements met."
