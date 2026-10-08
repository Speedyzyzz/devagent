"""Security validation layer for DevAgent sandbox containment."""
import fnmatch
from pathlib import Path
from backend.app.core.exceptions import (
    InvalidPathError,
    SandboxViolation,
    SensitiveFileAccessBlocked,
)

# Denied file patterns (case-insensitive where applicable)
SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "id_ed25519*",
    "id_dsa*",
    "id_ecdsa*",
    "credentials.json",
    "service_account.json",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
    ".git/config",
    "*/.git/config",
]


def is_sensitive_path(path: Path) -> bool:
    """Check if the given path matches any sensitive file patterns."""
    filename = path.name.lower()
    path_str = str(path).replace("\\", "/").lower()

    for pattern in SENSITIVE_PATTERNS:
        pattern_lower = pattern.lower()
        if fnmatch.fnmatch(filename, pattern_lower):
            return True
        if fnmatch.fnmatch(path_str, f"*{pattern_lower}*"):
            return True
        # Check specific parts like .git/config
        if "/.git/config" in path_str or path_str.endswith(".git/config"):
            return True

    return False


def resolve_sandbox_path(
    sandbox_root: Path,
    target_path: str | Path,
    must_exist: bool = False,
) -> Path:
    """
    Resolve a path relative to the sandbox root and verify strict containment.

    Protections enforced:
    - Path traversal attacks (../../)
    - Symlink escapes pointing outside sandbox_root
    - Absolute external paths (/etc/passwd, ~/.ssh)
    - Non-existent files when must_exist=True
    """
    # Canonicalize the sandbox root first (resolve symlinks in root itself)
    canonical_root = sandbox_root.resolve()

    raw_path = Path(target_path)

    # If the path is absolute, check if it starts with canonical_root
    if raw_path.is_absolute():
        candidate = raw_path
    else:
        candidate = canonical_root / raw_path

    # Canonicalize target (strict=False ensures containment is checked even if file does not exist)
    resolved_target = candidate.resolve(strict=False)

    # Verify that resolved path is strictly within canonical_root
    try:
        resolved_target.relative_to(canonical_root)
    except ValueError:
        raise SandboxViolation(
            f"Access denied: path '{target_path}' resolves outside sandbox root ({canonical_root})",
            details={
                "target_path": str(target_path),
                "resolved_target": str(resolved_target),
                "sandbox_root": str(canonical_root),
            },
        )

    # If must_exist is True, verify that the file/dir exists now
    if must_exist and not resolved_target.exists():
        raise InvalidPathError(f"Target path does not exist: {target_path}")

    return resolved_target


def validate_safe_path(
    sandbox_root: Path,
    target_path: str | Path,
    must_exist: bool = False,
) -> Path:
    """
    Complete path validation: containment check + sensitive file block.
    """
    resolved = resolve_sandbox_path(sandbox_root, target_path, must_exist=must_exist)

    if is_sensitive_path(resolved):
        raise SensitiveFileAccessBlocked(
            f"Access to sensitive file '{resolved.name}' is blocked by security policy",
            details={"path": str(resolved)},
        )

    return resolved
