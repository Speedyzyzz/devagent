"""Custom exceptions for DevAgent."""
from typing import Any


class DevAgentError(Exception):
    """Base exception for all DevAgent domain errors."""

    def __init__(self, message: str, error_code: str = "DEVAGENT_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class SandboxViolation(DevAgentError):
    """Raised when an operation attempts to access or modify paths outside the sandbox root."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="SANDBOX_VIOLATION", details=details)


class SensitiveFileAccessBlocked(DevAgentError):
    """Raised when an operation attempts to access protected/sensitive files."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="SENSITIVE_FILE_BLOCKED", details=details)


class InvalidPathError(DevAgentError):
    """Raised when a provided path is invalid or does not exist where required."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="INVALID_PATH", details=details)


class ReadLimitExceeded(DevAgentError):
    """Raised when a file read request exceeds the allowable line limit."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="READ_LIMIT_EXCEEDED", details=details)


class PatchError(DevAgentError):
    """Base class for patching errors."""

    def __init__(self, message: str, error_code: str = "PATCH_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code=error_code, details=details)


class PatchNotFound(PatchError):
    """Raised when the target block to replace is not found in the file."""

    def __init__(self, message: str = "Target block not found in file", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="PATCH_NOT_FOUND", details=details)


class PatchAmbiguous(PatchError):
    """Raised when the target block appears more than once in the file."""

    def __init__(self, occurrences: int, message: str = "Target block is ambiguous", details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["occurrences"] = occurrences
        super().__init__(
            f"{message}: found {occurrences} occurrences. Provide more surrounding context.",
            error_code="PATCH_AMBIGUOUS",
            details=merged,
        )


class SyntaxValidationError(PatchError):
    """Raised when patched code fails language syntax validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code="SYNTAX_VALIDATION_ERROR", details=details)


class VerificationError(DevAgentError):
    """Base class for verification runner errors."""

    def __init__(self, message: str, error_code: str = "VERIFICATION_ERROR", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, error_code=error_code, details=details)


class DisallowedRunner(VerificationError):
    """Raised when an unapproved runner command is submitted."""

    def __init__(self, runner: str, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["runner"] = runner
        super().__init__(f"Verification runner '{runner}' is not allowed", error_code="DISALLOWED_RUNNER", details=merged)


class VerificationTimeout(VerificationError):
    """Raised when a verification command exceeds the execution timeout."""

    def __init__(self, timeout_seconds: int, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["timeout_seconds"] = timeout_seconds
        super().__init__(f"Verification timed out after {timeout_seconds} seconds", error_code="VERIFICATION_TIMEOUT", details=merged)


class VerificationOutputExceeded(VerificationError):
    """Raised when verification output exceeds the character limit."""

    def __init__(self, char_count: int, max_chars: int, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["char_count"] = char_count
        merged["max_chars"] = max_chars
        super().__init__(f"Verification output exceeded limit ({char_count} > {max_chars})", error_code="OUTPUT_LIMIT_EXCEEDED", details=merged)


class ToolNotFoundError(DevAgentError):
    """Raised when an unknown tool name is invoked."""

    def __init__(self, tool_name: str, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["tool_name"] = tool_name
        super().__init__(f"Tool '{tool_name}' not found in registry", error_code="TOOL_NOT_FOUND", details=merged)


class BudgetExceededError(DevAgentError):
    """Raised when the agent exceeds configured iteration, tool call, or verification budgets."""

    def __init__(self, budget_type: str, limit: int, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["budget_type"] = budget_type
        merged["limit"] = limit
        super().__init__(f"Budget exceeded for {budget_type} (limit: {limit})", error_code="BUDGET_EXCEEDED", details=merged)


class SessionNotFoundError(DevAgentError):
    """Raised when a requested session cannot be located."""

    def __init__(self, session_id: str, details: dict[str, Any] | None = None) -> None:
        merged = details or {}
        merged["session_id"] = session_id
        super().__init__(f"Session '{session_id}' not found", error_code="SESSION_NOT_FOUND", details=merged)
