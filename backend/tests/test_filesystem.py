"""Unit tests for filesystem tools."""
from pathlib import Path
import pytest
from backend.app.agent.tools.filesystem import ListDirectoryTool, ReadFileLinesTool
from backend.app.core.exceptions import InvalidPathError, ReadLimitExceeded


@pytest.mark.asyncio
async def test_list_directory_basic(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ListDirectoryTool()

    result = await tool.execute(sandbox_root, {"path": "."})
    assert result.success is True
    assert result.data is not None

    names = [e["name"] for e in result.data["entries"]]
    assert "README.md" in names
    assert "src" in names

    # Crucial security assertion: sensitive files must never be exposed
    assert ".env" not in names
    assert ".git" not in names


@pytest.mark.asyncio
async def test_list_directory_nonexistent(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ListDirectoryTool()

    with pytest.raises(InvalidPathError):
        await tool.execute(sandbox_root, {"path": "nonexistent_folder"})


@pytest.mark.asyncio
async def test_read_file_lines_success(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ReadFileLinesTool()

    result = await tool.execute(sandbox_root, {"path": "src/main.py", "start_line": 1, "end_line": 10})
    assert result.success is True
    assert result.data is not None
    assert "   1 | print('hello world')" in result.data["content"]
    assert result.data["total_lines"] == 1


@pytest.mark.asyncio
async def test_read_file_lines_invalid_range(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ReadFileLinesTool()

    # start_line < 1
    res1 = await tool.execute(sandbox_root, {"path": "src/main.py", "start_line": 0, "end_line": 5})
    assert res1.success is False
    assert res1.error["code"] == "INVALID_LINE_RANGE"

    # end_line < start_line
    res2 = await tool.execute(sandbox_root, {"path": "src/main.py", "start_line": 5, "end_line": 2})
    assert res2.success is False
    assert res2.error["code"] == "INVALID_LINE_RANGE"


@pytest.mark.asyncio
async def test_read_file_lines_limit_exceeded(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = ReadFileLinesTool()

    with pytest.raises(ReadLimitExceeded):
        await tool.execute(sandbox_root, {"path": "src/main.py", "start_line": 1, "end_line": 200})
