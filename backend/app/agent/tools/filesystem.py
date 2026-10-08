"""Filesystem tools: list_directory and read_file_lines."""
import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from backend.app.agent.tools.base import BaseTool, ToolResult
from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    InvalidPathError,
    ReadLimitExceeded,
)
from backend.app.core.security import is_sensitive_path, validate_safe_path

IGNORED_NAMES = {
    ".git",
    ".env",
    "node_modules",
    "__pycache__",
    ".venv",
    ".pytest_cache",
    ".next",
    "dist",
    "build",
}


class ListDirectoryInput(BaseModel):
    path: str = Field(default=".", description="Relative path within the sandbox to list")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files and directories up to depth 2 with safety filters for workspace orientation."
    input_schema = ListDirectoryInput

    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        settings = get_settings()
        req_path = arguments.get("path", ".")

        safe_dir = validate_safe_path(sandbox_root, req_path, must_exist=True)
        if not safe_dir.is_dir():
            raise InvalidPathError(f"Target '{req_path}' is not a directory")

        entries: list[dict[str, str]] = []
        max_entries = settings.max_directory_entries
        max_depth = settings.max_directory_depth

        canonical_safe_dir = safe_dir.resolve()

        for root, dirs, files in os.walk(canonical_safe_dir):
            rel_root = Path(root).relative_to(canonical_safe_dir)
            current_depth = len(rel_root.parts)

            # Filter out ignored directories in-place so os.walk does not recurse into them
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_NAMES and not d.startswith(".") and not is_sensitive_path(Path(d))
            ]

            if current_depth >= max_depth:
                dirs.clear()
                continue

            for d in sorted(dirs):
                if len(entries) >= max_entries:
                    break
                entry_rel = (rel_root / d).as_posix() if str(rel_root) != "." else d
                entries.append({"name": entry_rel, "type": "directory"})

            for f in sorted(files):
                if len(entries) >= max_entries:
                    break
                if f in IGNORED_NAMES or f.startswith(".") or is_sensitive_path(Path(f)):
                    continue
                entry_rel = (rel_root / f).as_posix() if str(rel_root) != "." else f
                entries.append({"name": entry_rel, "type": "file"})

            if len(entries) >= max_entries:
                break

        return ToolResult.ok({
            "path": req_path,
            "entries_count": len(entries),
            "entries": entries,
            "truncated": len(entries) >= max_entries,
        })


class ReadFileInput(BaseModel):
    path: str = Field(..., description="Relative path of file to inspect")
    start_line: int = Field(default=1, description="1-indexed starting line number")
    end_line: int = Field(default=100, description="1-indexed ending line number (inclusive)")


class ReadFileLinesTool(BaseTool):
    name = "read_file_lines"
    description = "Read a specific range of lines from a file (up to 150 lines) with line numbers."
    input_schema = ReadFileInput

    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        settings = get_settings()
        req_path = arguments["path"]
        start_line = arguments.get("start_line", 1)
        end_line = arguments.get("end_line", 100)

        # Validation rules
        if start_line < 1:
            return ToolResult.fail("INVALID_LINE_RANGE", f"start_line must be >= 1, got {start_line}")
        if end_line < start_line:
            return ToolResult.fail("INVALID_LINE_RANGE", f"end_line ({end_line}) cannot be less than start_line ({start_line})")
        if (end_line - start_line + 1) > settings.max_read_file_lines:
            raise ReadLimitExceeded(
                f"Requested {end_line - start_line + 1} lines exceeds maximum allowed {settings.max_read_file_lines} lines",
                details={"requested": end_line - start_line + 1, "max_allowed": settings.max_read_file_lines},
            )

        safe_file = validate_safe_path(sandbox_root, req_path, must_exist=True)
        if not safe_file.is_file():
            raise InvalidPathError(f"Target '{req_path}' is not a file")

        try:
            with open(safe_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return ToolResult.fail("FILE_READ_ERROR", f"Could not read file '{req_path}': {str(e)}")

        total_lines = len(lines)
        if total_lines == 0:
            return ToolResult.ok({
                "path": req_path,
                "total_lines": 0,
                "content": "<empty file>",
            })

        actual_start = max(1, start_line)
        actual_end = min(total_lines, end_line)

        formatted_lines = []
        for line_num in range(actual_start, actual_end + 1):
            line_text = lines[line_num - 1].rstrip("\r\n")
            formatted_lines.append(f"{line_num:4d} | {line_text}")

        return ToolResult.ok({
            "path": req_path,
            "start_line": actual_start,
            "end_line": actual_end,
            "total_lines": total_lines,
            "content": "\n".join(formatted_lines),
        })
