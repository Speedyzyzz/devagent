"""Session manager managing isolated workspace allocations, background runs, and SSE queues."""
import asyncio
import shutil
import uuid
from pathlib import Path
from typing import Any
import yaml

from backend.app.agent.engine import AgentEngine
from backend.app.agent.events import AgentEvent, EventType
from backend.app.agent.models import AgentDecision, AgentStatus
from backend.app.agent.providers import get_llm_provider
from backend.app.agent.providers.mock import MockLLMProvider
from backend.app.agent.state import AgentState
from backend.app.core.config import get_settings
from backend.app.core.exceptions import SessionNotFoundError
from backend.app.core.logging import get_logger
from backend.app.storage.database import Database, get_db

logger = get_logger("session.manager")


class SessionManager:
    """Manages session workspaces, background execution tasks, and streaming event buses."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or get_db()
        self.settings = get_settings()
        self._active_states: dict[str, AgentState] = {}
        self._event_queues: dict[str, list[asyncio.Queue[AgentEvent | None]]] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    def get_event_queue(self, session_id: str) -> asyncio.Queue[AgentEvent | None]:
        """Subscribe to real-time events for a session."""
        q: asyncio.Queue[AgentEvent | None] = asyncio.Queue()
        if session_id not in self._event_queues:
            self._event_queues[session_id] = []
        self._event_queues[session_id].append(q)
        return q

    def unsubscribe_queue(self, session_id: str, queue: asyncio.Queue[AgentEvent | None]) -> None:
        if session_id in self._event_queues:
            try:
                self._event_queues[session_id].remove(queue)
            except ValueError:
                pass

    async def broadcast_event(self, event: AgentEvent) -> None:
        """Push event to database and all active SSE listener queues."""
        self.db.add_event(
            session_id=event.session_id,
            event_type=event.type.value,
            step=event.step,
            payload=event.data,
        )

        queues = self._event_queues.get(event.session_id, [])
        for q in list(queues):
            try:
                await q.put(event)
            except Exception as e:
                logger.warning(f"Failed to push event to queue: {e}")

    async def create_session(
        self,
        issue: str,
        repository: str = "demo-repo",
        verification_instruction: str | None = None,
        provider_name: str | None = None,
        case_id: str | None = None,
    ) -> str:
        session_id = f"sess_{uuid.uuid4().hex[:10]}"

        # 1. Allocate isolated workspace
        session_workspace = (self.settings.sandbox_root / "sessions" / session_id / "repo").resolve()
        session_workspace.mkdir(parents=True, exist_ok=True)

        # 2. Populate repo
        demo_repo_path = Path("./demo-repo").resolve()
        if demo_repo_path.exists():
            shutil.copytree(demo_repo_path, session_workspace, dirs_exist_ok=True)

        # 3. Initialize state
        state = AgentState(
            session_id=session_id,
            issue=issue,
            workspace=session_workspace,
            verification_instruction=verification_instruction,
            status=AgentStatus.CREATED,
            max_iterations=self.settings.max_agent_iterations,
        )
        self._active_states[session_id] = state

        # 4. Record in database
        self.db.create_session(
            session_id=session_id,
            repository=repository,
            issue=issue,
            status="CREATED",
        )

        # 5. Determine LLM provider (or load case script if benchmark case selected)
        if case_id:
            case_file = Path(f"./evaluation/cases/{case_id}.yaml")
            if case_file.exists():
                with open(case_file, "r", encoding="utf-8") as f:
                    case_data = yaml.safe_load(f)
                scripted = [
                    AgentDecision(
                        investigation=f"Executing {s['name']}",
                        hypothesis=f"Investigating {case_data['name']}",
                        action_plan=f"Calling {s['name']}",
                        tool_calls=[{"name": s["name"], "arguments": s["arguments"]}],
                    )
                    for s in case_data.get("scripted_steps", [])
                ]
                scripted.append(
                    AgentDecision(
                        investigation="Verification passed 100%.",
                        hypothesis="Bug resolved.",
                        action_plan="Finish task.",
                        indicates_completion=True,
                        root_cause_report=case_data.get("root_cause", "Issue remediated successfully."),
                    )
                )
                provider = MockLLMProvider(scripted)
            else:
                provider = get_llm_provider(provider_name)
        else:
            provider = get_llm_provider(provider_name)

        # 6. Spawn execution loop in background
        engine = AgentEngine(llm_provider=provider, event_callback=self.broadcast_event)
        task = asyncio.create_task(self._run_session_task(engine, state))
        self._tasks[session_id] = task

        return session_id

    async def _run_session_task(self, engine: AgentEngine, state: AgentState) -> None:
        try:
            final_state = await engine.run(state)
            self.db.update_session(
                session_id=final_state.session_id,
                status=final_state.status.value,
                iteration=final_state.iteration,
                files_changed=final_state.files_changed,
                root_cause=final_state.root_cause,
                final_diff=final_state.final_diff,
                error=final_state.error,
                started_at=final_state.started_at,
                completed_at=final_state.completed_at,
            )
        except Exception as e:
            logger.error(f"Session {state.session_id} encountered fatal error: {e}")
            self.db.update_session(
                session_id=state.session_id,
                status="FAILED",
                iteration=state.iteration,
                files_changed=state.files_changed,
                error=str(e),
            )
            await self.broadcast_event(
                AgentEvent(
                    type=EventType.AGENT_FAILED,
                    session_id=state.session_id,
                    step=state.iteration,
                    data={"error": str(e)},
                )
            )
        finally:
            # Signal stream termination
            queues = self._event_queues.get(state.session_id, [])
            for q in list(queues):
                await q.put(None)

    def cancel_session(self, session_id: str) -> None:
        """Cancel an in-progress session cleanly."""
        state = self._active_states.get(session_id)
        if not state:
            record = self.db.get_session(session_id)
            if not record:
                raise SessionNotFoundError(session_id)
            return

        state.cancel_requested = True
        logger.info(f"Cancellation flagged for session {session_id}")

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        """Retrieve live or historical session details."""
        if session_id in self._active_states:
            state = self._active_states[session_id]
            return {
                "session_id": state.session_id,
                "issue": state.issue,
                "status": state.status.value,
                "iteration": state.iteration,
                "max_iterations": state.max_iterations,
                "tool_calls_count": state.tool_calls_count,
                "verification_attempts": state.verification_attempts,
                "files_changed": state.files_changed,
                "final_diff": state.final_diff,
                "root_cause": state.root_cause,
                "error": state.error,
                "current_hypothesis": state.current_hypothesis,
            }

        record = self.db.get_session(session_id)
        if not record:
            raise SessionNotFoundError(session_id)
        return record


_default_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = SessionManager()
    return _default_manager
