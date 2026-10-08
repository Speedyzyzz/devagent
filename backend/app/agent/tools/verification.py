"""Structured verification runner tool for executing sandboxed test suites."""
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from backend.app.agent.tools.base import BaseTool, ToolResult
from backend.app.core.config import get_settings
from backend.app.core.exceptions import (
    DisallowedRunner,
    VerificationTimeout,
)
from backend.app.core.security import validate_safe_path

ALLOWED_RUNNERS = {
    "pytest",
    "python -m pytest",
    "python3 -m pytest",
    "npm test",
    "npm run lint",
    "npm run typecheck",
}


class VerificationInput(BaseModel):
    runner: str = Field(default="pytest", description="Allowed runner: 'pytest', 'python -m pytest', 'npm test'")
    args: list[str] = Field(default_factory=list, description="Target test files or arguments, e.g. ['tests/test_cart.py']")
    cwd: str = Field(default=".", description="Subdirectory within the workspace to run tests from")


class ExecuteVerificationTool(BaseTool):
    name = "execute_verification"
    description = "Execute an authorized test runner (e.g. pytest) against the workspace to verify fixes."
    input_schema = VerificationInput

    async def execute(self, sandbox_root: Path, arguments: dict[str, Any]) -> ToolResult:
        settings = get_settings()
        runner = arguments.get("runner", "pytest").strip()
        args = arguments.get("args", [])
        rel_cwd = arguments.get("cwd", ".")

        if runner not in ALLOWED_RUNNERS:
            raise DisallowedRunner(runner, details={"allowed_runners": list(ALLOWED_RUNNERS)})

        work_dir = validate_safe_path(sandbox_root, rel_cwd, must_exist=True)

        # Construct execution command arguments safely without shell invocation
        if runner in ("pytest", "python -m pytest", "python3 -m pytest"):
            # Point to active python executable (e.g. current venv)
            exec_binary = sys.executable
            cmd = [exec_binary, "-m", "pytest"] + list(args)
        elif runner.startswith("npm "):
            npm_binary = "npm"
            cmd = [npm_binary] + runner.split()[1:] + list(args)
        else:
            cmd = [runner] + list(args)

        # Prevent sub-processes from leaking sensitive environment variables
        env = os.environ.copy()
        # Ensure workspace root is in PYTHONPATH
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{sandbox_root.resolve()}:{existing_pythonpath}"

        start_time = time.monotonic()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(work_dir.resolve()),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=float(settings.verification_timeout_seconds),
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except ProcessLookupError:
                pass
            raise VerificationTimeout(settings.verification_timeout_seconds)
        except Exception as e:
            return ToolResult.fail("EXECUTION_ERROR", f"Failed to execute verification runner: {str(e)}")

        duration = round(time.monotonic() - start_time, 2)
        stdout_text = stdout_bytes.decode("utf-8", errors="replace")
        stderr_text = stderr_bytes.decode("utf-8", errors="replace")

        max_chars = settings.max_verification_output_chars
        truncated = False

        if len(stdout_text) > max_chars:
            stdout_text = stdout_text[:max_chars] + f"\n... [Output truncated at {max_chars} chars]"
            truncated = True

        if len(stderr_text) > max_chars:
            stderr_text = stderr_text[:max_chars] + f"\n... [Output truncated at {max_chars} chars]"
            truncated = True

        passed = (process.returncode == 0)

        return ToolResult.ok({
            "runner": runner,
            "args": args,
            "exit_code": process.returncode,
            "passed": passed,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "duration_seconds": duration,
            "truncated": truncated,
        })
