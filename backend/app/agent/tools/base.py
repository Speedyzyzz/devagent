"""Base class, ToolResult schema, and registry for DevAgent tools."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Type
from pydantic import BaseModel, Field
from backend.app.core.exceptions import DevAgentError, ToolNotFoundError


class ToolResult(BaseModel):
    """Standardized response contract for all tool executions."""

    success: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, data: dict[str, Any], metadata: dict[str, Any] | None = None) -> "ToolResult":
        return cls(success=True, data=data, metadata=metadata or {})

    @classmethod
    def fail(cls, error_code: str, message: str, details: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> "ToolResult":
        return cls(
            success=False,
            error={
                "code": error_code,
                "message": message,
                "details": details or {},
            },
            metadata=metadata or {},
        )


class BaseTool(ABC):
    """Abstract base class for all sandboxed tools."""

    name: str
    description: str
    input_schema: Type[BaseModel]

    @abstractmethod
    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        """Execute the tool safely within the specified sandbox root."""
        pass


class ToolRegistry:
    """Centralized registry for tool discovery, validation, and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    def get_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in standard tool-calling format."""
        definitions = []
        for tool in self._tools.values():
            schema = tool.input_schema.model_json_schema()
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": schema,
                },
            })
        return definitions

    async def execute(self, tool_name: str, arguments: dict[str, Any], sandbox_root: Path) -> ToolResult:
        """
        Execute tool with input validation, error trapping, and structured result return.
        Never lets raw tracebacks reach the agent.
        """
        tool = self.get(tool_name)
        try:
            # Pydantic input validation
            validated_args = tool.input_schema.model_validate(arguments).model_dump()
            return await tool.execute(sandbox_root, validated_args)
        except DevAgentError as e:
            return ToolResult.fail(
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )
        except Exception as e:
            return ToolResult.fail(
                error_code="UNEXPECTED_ERROR",
                message=f"An unexpected error occurred during tool execution: {str(e)}",
            )
