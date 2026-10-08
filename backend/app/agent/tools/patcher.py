"""Atomic, syntax-validated patch application tool."""
import ast
import difflib
import os
import uuid
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from backend.app.agent.tools.base import BaseTool, ToolResult
from backend.app.core.exceptions import (
    InvalidPathError,
    PatchAmbiguous,
    PatchNotFound,
    SyntaxValidationError,
)
from backend.app.core.security import validate_safe_path


class SyntaxValidator:
    """Pluggable syntax validator across supported file types."""

    @staticmethod
    def validate(file_path: Path, content: str) -> None:
        extension = file_path.suffix.lower()

        if extension == ".py":
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                raise SyntaxValidationError(
                    f"Python syntax validation failed on line {e.lineno}, col {e.offset}: {e.msg}",
                    details={
                        "lineno": e.lineno,
                        "offset": e.offset,
                        "syntax_error": e.msg,
                    },
                )


class ApplyPatchInput(BaseModel):
    path: str = Field(..., description="Target file path relative to sandbox root")
    search_block: str = Field(..., description="Exact snippet to find and replace")
    replace_block: str = Field(..., description="Exact replacement snippet")


class ApplyPatchTool(BaseTool):
    name = "apply_patch"
    description = "Apply an exact-match block patch atomically with syntax validation and unified diff output."
    input_schema = ApplyPatchInput

    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        rel_path = arguments["path"]
        search_block = arguments["search_block"]
        replace_block = arguments["replace_block"]

        safe_path = validate_safe_path(sandbox_root, rel_path, must_exist=True)
        if not safe_path.is_file():
            raise InvalidPathError(f"Target '{rel_path}' is not a regular file")

        try:
            with open(safe_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            return ToolResult.fail("FILE_READ_ERROR", f"Could not read '{rel_path}': {str(e)}")

        # Normalize line endings for comparison if necessary
        normalized_search = search_block.replace("\r\n", "\n")
        normalized_replace = replace_block.replace("\r\n", "\n")
        normalized_original = original_content.replace("\r\n", "\n")

        # Check occurrence count
        occurrences = normalized_original.count(normalized_search)

        if occurrences == 0:
            raise PatchNotFound(
                f"search_block was not found in '{rel_path}'. Verify exact whitespace, indentation, and lines."
            )

        if occurrences > 1:
            raise PatchAmbiguous(
                occurrences=occurrences,
                message=f"search_block appears {occurrences} times in '{rel_path}'",
            )

        # Replace exact single block
        new_content = normalized_original.replace(normalized_search, normalized_replace, 1)

        # Step 1: Pre-validation of syntax
        SyntaxValidator.validate(safe_path, new_content)

        # Step 2: Atomic write via temporary file in target directory
        temp_file = safe_path.parent / f".{safe_path.name}.{uuid.uuid4().hex}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(new_content)
                f.flush()
                os.fsync(f.fileno())

            # Step 3: Atomic replace (guaranteed atomic on same filesystem)
            os.replace(temp_file, safe_path)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return ToolResult.fail("WRITE_ERROR", f"Failed to perform atomic replacement: {str(e)}")

        # Step 4: Generate unified diff
        orig_lines = normalized_original.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff_lines = list(
            difflib.unified_diff(
                orig_lines,
                new_lines,
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            )
        )
        unified_diff = "".join(diff_lines)

        return ToolResult.ok({
            "path": rel_path,
            "patch_applied": True,
            "diff": unified_diff,
            "lines_added": sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++")),
            "lines_removed": sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---")),
        })
