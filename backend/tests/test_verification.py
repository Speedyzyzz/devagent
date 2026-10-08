"""Unit tests for ExecuteVerificationTool."""
from pathlib import Path
import pytest
from backend.app.agent.tools.verification import ExecuteVerificationTool
from backend.app.core.exceptions import DisallowedRunner


@pytest.mark.asyncio
async def test_verification_pytest_success(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    test_file = sandbox_root / "test_ok.py"
    test_file.write_text("def test_always_passes():\n    assert 1 + 1 == 2\n")

    tool = ExecuteVerificationTool()
    result = await tool.execute(sandbox_root, {
        "runner": "pytest",
        "args": ["test_ok.py"],
    })

    assert result.success is True
    assert result.data["passed"] is True
    assert result.data["exit_code"] == 0
    assert "1 passed" in result.data["stdout"]


@pytest.mark.asyncio
async def test_verification_pytest_failure(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    test_file = sandbox_root / "test_bad.py"
    test_file.write_text("def test_fails():\n    assert 1 == 999\n")

    tool = ExecuteVerificationTool()
    result = await tool.execute(sandbox_root, {
        "runner": "pytest",
        "args": ["test_bad.py"],
    })

    assert result.success is True
    assert result.data["passed"] is False
    assert result.data["exit_code"] != 0
    assert "1 failed" in result.data["stdout"] or "FAILED" in result.data["stdout"]


@pytest.mark.asyncio
async def test_verification_disallowed_runner(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ExecuteVerificationTool()

    with pytest.raises(DisallowedRunner):
        await tool.execute(sandbox_root, {
            "runner": "bash",
            "args": ["-c", "echo dangerous"],
        })

    with pytest.raises(DisallowedRunner):
        await tool.execute(sandbox_root, {
            "runner": "rm -rf",
            "args": ["/"],
        })
