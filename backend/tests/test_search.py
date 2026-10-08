"""Unit tests for SearchCodeTool."""
from pathlib import Path
import pytest
from backend.app.agent.tools.search import SearchCodeTool


@pytest.mark.asyncio
async def test_search_code_exact_match(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = SearchCodeTool()

    result = await tool.execute(sandbox_root, {"query": "def add"})
    assert result.success is True
    assert result.data is not None
    assert result.data["matches_count"] >= 1
    match = result.data["matches"][0]
    assert "utils.py" in match["file"]
    assert match["line"] == 1
    assert "def add(a, b):" in match["preview"]


@pytest.mark.asyncio
async def test_search_code_extension_filter(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = SearchCodeTool()

    # Searching for 'Workspace' with .md extension should find README.md
    res_md = await tool.execute(sandbox_root, {"query": "Workspace", "extension": ".md"})
    assert res_md.success is True
    assert res_md.data["matches_count"] == 1
    assert res_md.data["matches"][0]["file"] == "README.md"

    # Searching for 'Workspace' with .py extension should find nothing
    res_py = await tool.execute(sandbox_root, {"query": "Workspace", "extension": ".py"})
    assert res_py.success is True
    assert res_py.data["matches_count"] == 0


@pytest.mark.asyncio
async def test_search_code_ignores_sensitive_and_hidden(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    tool = SearchCodeTool()

    # Querying secret token in .env must return 0 matches
    result = await tool.execute(sandbox_root, {"query": "SECRET_TOKEN"})
    assert result.success is True
    assert result.data["matches_count"] == 0


@pytest.mark.asyncio
async def test_search_code_skips_binary(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    bin_file = sandbox_root / "src" / "binary.dat"
    bin_file.write_bytes(b"\x00\x01\x02\x03FINDME_IN_BINARY\x00")

    tool = SearchCodeTool()
    result = await tool.execute(sandbox_root, {"query": "FINDME_IN_BINARY"})
    assert result.success is True
    assert result.data["matches_count"] == 0
