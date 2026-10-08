"""Tools module providing the centralized ToolRegistry with default tools registered."""
from backend.app.agent.tools.base import BaseTool, ToolRegistry, ToolResult
from backend.app.agent.tools.filesystem import ListDirectoryTool, ReadFileLinesTool
from backend.app.agent.tools.patcher import ApplyPatchTool
from backend.app.agent.tools.search import SearchCodeTool
from backend.app.agent.tools.verification import ExecuteVerificationTool


def create_default_registry() -> ToolRegistry:
    """Create and populate the default registry with the 5 core deterministic tools."""
    registry = ToolRegistry()
    registry.register(ListDirectoryTool())
    registry.register(SearchCodeTool())
    registry.register(ReadFileLinesTool())
    registry.register(ApplyPatchTool())
    registry.register(ExecuteVerificationTool())
    return registry


__all__ = [
    "BaseTool",
    "ToolRegistry",
    "ToolResult",
    "ListDirectoryTool",
    "ReadFileLinesTool",
    "SearchCodeTool",
    "ApplyPatchTool",
    "ExecuteVerificationTool",
    "create_default_registry",
]
