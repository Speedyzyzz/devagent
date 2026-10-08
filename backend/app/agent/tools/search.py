"""Code search tool supporting ripgrep and high-performance Python regex fallback."""
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from backend.app.agent.tools.base import BaseTool, ToolResult
from backend.app.core.config import get_settings
from backend.app.core.exceptions import InvalidPathError
from backend.app.core.security import is_sensitive_path, validate_safe_path

IGNORED_DIRS = {
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


def is_binary_file(file_path: Path) -> bool:
    """Check if file appears to be binary by inspecting first 1024 bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except OSError:
        return True


class SearchCodeInput(BaseModel):
    query: str = Field(..., description="Text query or regex pattern to search for")
    extension: str | None = Field(default=None, description="Optional extension filter, e.g. '.py' or '.ts'")
    path: str = Field(default=".", description="Subdirectory within workspace to search")


class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search codebase for keywords or regex patterns with extension filters and result limits."
    input_schema = SearchCodeInput

    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        settings = get_settings()
        query = arguments["query"].strip()
        extension = arguments.get("extension")
        sub_path = arguments.get("path", ".")

        if not query:
            return ToolResult.fail("EMPTY_QUERY", "Search query cannot be empty")

        safe_search_dir = validate_safe_path(sandbox_root, sub_path, must_exist=True)
        if not safe_search_dir.is_dir():
            raise InvalidPathError(f"Search target '{sub_path}' is not a directory")

        max_matches = settings.max_search_matches
        rg_binary = shutil.which("rg")

        if rg_binary:
            return self._execute_ripgrep(
                rg_binary=rg_binary,
                sandbox_root=sandbox_root,
                search_dir=safe_search_dir,
                query=query,
                extension=extension,
                max_matches=max_matches,
            )
        else:
            return self._execute_python_search(
                sandbox_root=sandbox_root,
                search_dir=safe_search_dir,
                query=query,
                extension=extension,
                max_matches=max_matches,
            )

    def _execute_ripgrep(
        self,
        rg_binary: str,
        sandbox_root: Path,
        search_dir: Path,
        query: str,
        extension: str | None,
        max_matches: int,
    ) -> ToolResult:
        cmd = [
            rg_binary,
            "--line-number",
            "--max-count", str(max_matches),
            "--color", "never",
            "--no-heading",
        ]

        if extension:
            ext_clean = extension if extension.startswith(".") else f".{extension}"
            cmd.extend(["--glob", f"*{ext_clean}"])

        for ign in IGNORED_DIRS:
            cmd.extend(["--glob", f"!**/{ign}/**", "--glob", f"!**/{ign}"])

        cmd.extend(["--", query, str(search_dir)])

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return ToolResult.fail("SEARCH_TIMEOUT", "ripgrep command timed out")

        matches: list[dict[str, Any]] = []
        for line in res.stdout.splitlines():
            if len(matches) >= max_matches:
                break
            parts = line.split(":", 2)
            if len(parts) >= 3:
                full_path_str = parts[0]
                line_no_str = parts[1]
                preview_str = parts[2].strip()

                try:
                    p = Path(full_path_str).resolve()
                    if is_sensitive_path(p):
                        continue
                    rel_to_sandbox = p.relative_to(sandbox_root.resolve()).as_posix()
                    line_no = int(line_no_str)
                    matches.append({
                        "file": rel_to_sandbox,
                        "line": line_no,
                        "preview": preview_str[:200],
                    })
                except (ValueError, ValueError):
                    continue

        return ToolResult.ok({
            "query": query,
            "engine": "ripgrep",
            "matches_count": len(matches),
            "matches": matches,
            "truncated": len(matches) >= max_matches,
        })

    def _execute_python_search(
        self,
        sandbox_root: Path,
        search_dir: Path,
        query: str,
        extension: str | None,
        max_matches: int,
    ) -> ToolResult:
        """High-performance Python regex fallback engine with identical semantics."""
        try:
            pattern = re.compile(query, re.IGNORECASE)
        except re.error:
            # Fallback to literal search if regex is invalid
            pattern = re.compile(re.escape(query), re.IGNORECASE)

        matches: list[dict[str, Any]] = []
        canonical_sandbox = sandbox_root.resolve()
        canonical_search_dir = search_dir.resolve()

        if extension:
            target_ext = extension if extension.startswith(".") else f".{extension}"
            target_ext = target_ext.lower()
        else:
            target_ext = None

        for root, dirs, files in os.walk(canonical_search_dir):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_DIRS and not d.startswith(".") and not is_sensitive_path(Path(d))
            ]

            for file_name in sorted(files):
                if file_name in IGNORED_DIRS or file_name.startswith(".") or is_sensitive_path(Path(file_name)):
                    continue

                if target_ext and not file_name.lower().endswith(target_ext):
                    continue

                file_path = Path(root) / file_name

                # Skip binary files
                if is_binary_file(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        for idx, line in enumerate(f, start=1):
                            if pattern.search(line):
                                rel_path = file_path.resolve().relative_to(canonical_sandbox).as_posix()
                                matches.append({
                                    "file": rel_path,
                                    "line": idx,
                                    "preview": line.strip()[:200],
                                })
                                if len(matches) >= max_matches:
                                    break
                except OSError:
                    continue

                if len(matches) >= max_matches:
                    break

            if len(matches) >= max_matches:
                break

        return ToolResult.ok({
            "query": query,
            "engine": "python_regex",
            "matches_count": len(matches),
            "matches": matches,
            "truncated": len(matches) >= max_matches,
        })
