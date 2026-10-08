"""Integration tests for the Agent Engine using deterministic MockLLMProvider."""
from pathlib import Path
import pytest
from backend.app.agent.engine import AgentEngine
from backend.app.agent.models import AgentDecision, AgentStatus
from backend.app.agent.providers.mock import MockLLMProvider
from backend.app.agent.state import AgentState


@pytest.mark.asyncio
async def test_mock_agent_solves_bug_end_to_end(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    # Prepare buggy workspace
    calc_file = sandbox_root / "calculator.py"
    calc_file.write_text("def add(a, b):\n    return a - b\n")

    test_file = sandbox_root / "test_calc.py"
    test_file.write_text("from calculator import add\n\ndef test_add():\n    assert add(2, 3) == 5\n")

    scripted_turns = [
        # Turn 1: Orient
        AgentDecision(
            investigation="Starting reconnaissance.",
            hypothesis="Need to inspect workspace structure.",
            action_plan="List directory contents.",
            tool_calls=[{"name": "list_directory", "arguments": {"path": "."}}],
        ),
        # Turn 2: Search
        AgentDecision(
            investigation="Identified calculator.py and test_calc.py.",
            hypothesis="Bug is likely in calculator.py.",
            action_plan="Search for 'def add'.",
            tool_calls=[{"name": "search_code", "arguments": {"query": "def add"}}],
        ),
        # Turn 3: Read
        AgentDecision(
            investigation="Found def add in calculator.py line 1.",
            hypothesis="add function performs subtraction instead of addition.",
            action_plan="Read lines around def add.",
            tool_calls=[{"name": "read_file_lines", "arguments": {"path": "calculator.py", "start_line": 1, "end_line": 5}}],
        ),
        # Turn 4: Patch
        AgentDecision(
            investigation="Confirmed line 2: 'return a - b'.",
            hypothesis="Replace subtraction with addition.",
            action_plan="Apply patch to calculator.py.",
            tool_calls=[{
                "name": "apply_patch",
                "arguments": {
                    "path": "calculator.py",
                    "search_block": "return a - b",
                    "replace_block": "return a + b",
                },
            }],
        ),
        # Turn 5: Verify
        AgentDecision(
            investigation="Patch applied successfully.",
            hypothesis="Tests should now pass.",
            action_plan="Execute pytest test_calc.py.",
            tool_calls=[{
                "name": "execute_verification",
                "arguments": {"runner": "pytest", "args": ["test_calc.py"]},
            }],
        ),
        # Turn 6: Conclude
        AgentDecision(
            investigation="Verification passed 100%.",
            hypothesis="Fix verified.",
            action_plan="Declare completion.",
            indicates_completion=True,
            root_cause_report="calculator.py add function returned a - b instead of a + b.",
        ),
    ]

    mock_llm = MockLLMProvider(scripted_turns)
    engine = AgentEngine(llm_provider=mock_llm)

    state = AgentState(
        session_id="test_session_001",
        issue="Fix addition bug in calculator",
        workspace=sandbox_root,
        max_iterations=8,
    )

    final_state = await engine.run(state)

    # Core engine assertions
    assert final_state.status == AgentStatus.COMPLETED
    assert final_state.has_passed_verification() is True
    assert "calculator.py" in final_state.files_changed
    assert "+    return a + b" in (final_state.final_diff or "")
    assert final_state.root_cause is not None
    assert "add function returned a - b" in final_state.root_cause


@pytest.mark.asyncio
async def test_engine_blocks_premature_completion(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    # Mock attempts to claim completion immediately without patching or testing
    scripted_turns = [
        AgentDecision(
            investigation="I looked at the code.",
            hypothesis="It looks fine.",
            action_plan="Done.",
            indicates_completion=True,
            root_cause_report="No fix needed.",
        )
    ]

    mock_llm = MockLLMProvider(scripted_turns)
    engine = AgentEngine(llm_provider=mock_llm)

    state = AgentState(
        session_id="test_session_002",
        issue="Test premature completion block",
        workspace=sandbox_root,
        max_iterations=2,
    )

    final_state = await engine.run(state)

    # Engine MUST NOT allow completion without modified files and passing tests
    assert final_state.status == AgentStatus.FAILED
    assert "maximum iteration budget" in (final_state.error or "")


@pytest.mark.asyncio
async def test_engine_cancellation(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    scripted_turns = [
        AgentDecision(
            action_plan="List directory",
            tool_calls=[{"name": "list_directory", "arguments": {"path": "."}}],
        )
    ]

    mock_llm = MockLLMProvider(scripted_turns)
    engine = AgentEngine(llm_provider=mock_llm)

    state = AgentState(
        session_id="test_session_003",
        issue="Test cancellation",
        workspace=sandbox_root,
        max_iterations=5,
    )
    state.cancel_requested = True

    final_state = await engine.run(state)
    assert final_state.status == AgentStatus.CANCELLED
