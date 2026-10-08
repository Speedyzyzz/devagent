"""Unit tests for ApplyPatchTool."""
from pathlib import Path
import pytest
from backend.app.agent.tools.patcher import ApplyPatchTool
from backend.app.core.exceptions import (
    PatchAmbiguous,
    PatchNotFound,
    SandboxViolation,
    SyntaxValidationError,
)


@pytest.mark.asyncio
async def test_apply_patch_success(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ApplyPatchTool()

    target_file = sandbox_root / "src" / "utils.py"
    original_code = target_file.read_text()

    result = await tool.execute(sandbox_root, {
        "path": "src/utils.py",
        "search_block": "return a + b",
        "replace_block": "return (a + b) * 2",
    })

    assert result.success is True
    assert result.data["patch_applied"] is True
    assert "--- a/src/utils.py" in result.data["diff"]
    assert "+++ b/src/utils.py" in result.data["diff"]
    assert "+    return (a + b) * 2" in result.data["diff"]

    updated_code = target_file.read_text()
    assert "return (a + b) * 2" in updated_code
    assert updated_code != original_code


@pytest.mark.asyncio
async def test_apply_patch_not_found(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ApplyPatchTool()

    with pytest.raises(PatchNotFound):
        await tool.execute(sandbox_root, {
            "path": "src/utils.py",
            "search_block": "nonexistent_code_snippet()",
            "replace_block": "something_else()",
        })


@pytest.mark.asyncio
async def test_apply_patch_ambiguous(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    dup_file = sandbox_root / "src" / "duplicate.py"
    dup_file.write_text("x = 1\nx = 1\n")

    tool = ApplyPatchTool()
    with pytest.raises(PatchAmbiguous) as exc_info:
        await tool.execute(sandbox_root, {
            "path": "src/duplicate.py",
            "search_block": "x = 1",
            "replace_block": "x = 2",
        })
    assert exc_info.value.details["occurrences"] == 2


@pytest.mark.asyncio
async def test_apply_patch_syntax_validation(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    target_file = sandbox_root / "src" / "utils.py"
    original_code = target_file.read_text()

    tool = ApplyPatchTool()
    with pytest.raises(SyntaxValidationError):
        await tool.execute(sandbox_root, {
            "path": "src/utils.py",
            "search_block": "return a + b",
            "replace_block": "def invalid_syntax_here( :",
        })

    # CRITICAL: Atomic guarantee — original file must NOT have been modified
    assert target_file.read_text() == original_code


@pytest.mark.asyncio
async def test_apply_patch_outside_sandbox(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ApplyPatchTool()

    with pytest.raises(SandboxViolation):
        await tool.execute(sandbox_root, {
            "path": "../../outside.txt",
            "search_block": "foo",
            "replace_block": "bar",
        })
