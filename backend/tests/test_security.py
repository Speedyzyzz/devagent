"""Comprehensive tests for sandbox security validation."""
from pathlib import Path
import pytest
from backend.app.core.exceptions import (
    InvalidPathError,
    SandboxViolation,
    SensitiveFileAccessBlocked,
)
from backend.app.core.security import (
    is_sensitive_path,
    resolve_sandbox_path,
    validate_safe_path,
)


def test_safe_path_allowed(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    # Relative safe path
    resolved = validate_safe_path(sandbox_root, "src/main.py", must_exist=True)
    assert resolved == (sandbox_root / "src" / "main.py").resolve()

    # Relative root file
    resolved_readme = validate_safe_path(sandbox_root, "README.md", must_exist=True)
    assert resolved_readme == (sandbox_root / "README.md").resolve()

    # Safe internal symlink
    safe_symlink = sandbox_env["safe_symlink"]
    if safe_symlink.exists():
        resolved_link = validate_safe_path(sandbox_root, "safe_link", must_exist=True)
        assert resolved_link == (sandbox_root / "README.md").resolve()


def test_path_traversal_blocked(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    # Direct traversal
    with pytest.raises(SandboxViolation) as exc_info:
        validate_safe_path(sandbox_root, "../../etc/passwd")
    assert "resolves outside sandbox root" in str(exc_info.value)

    # Subdirectory traversal escaping root
    with pytest.raises(SandboxViolation) as exc_info:
        validate_safe_path(sandbox_root, "src/../../../outside_secret.txt")
    assert "resolves outside sandbox root" in str(exc_info.value)


def test_absolute_path_blocked(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    outside_secret = sandbox_env["outside_secret"]

    with pytest.raises(SandboxViolation):
        validate_safe_path(sandbox_root, str(outside_secret))

    with pytest.raises(SandboxViolation):
        validate_safe_path(sandbox_root, "/etc/passwd")


def test_symlink_escape_blocked(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]
    escape_symlink = sandbox_env["escape_symlink"]

    if escape_symlink.is_symlink():
        with pytest.raises(SandboxViolation) as exc_info:
            validate_safe_path(sandbox_root, "escape_link")
        assert "resolves outside sandbox root" in str(exc_info.value)


def test_env_files_blocked(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    with pytest.raises(SensitiveFileAccessBlocked):
        validate_safe_path(sandbox_root, ".env")

    with pytest.raises(SensitiveFileAccessBlocked):
        validate_safe_path(sandbox_root, ".env.local")


def test_git_config_blocked(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    with pytest.raises(SensitiveFileAccessBlocked):
        validate_safe_path(sandbox_root, ".git/config")


def test_key_and_pem_patterns_blocked() -> None:
    assert is_sensitive_path(Path("id_rsa")) is True
    assert is_sensitive_path(Path("id_rsa.pub")) is True
    assert is_sensitive_path(Path("id_ed25519")) is True
    assert is_sensitive_path(Path("server.key")) is True
    assert is_sensitive_path(Path("cert.pem")) is True
    assert is_sensitive_path(Path("credentials.json")) is True
    assert is_sensitive_path(Path("safe_script.py")) is False
    assert is_sensitive_path(Path("utils.ts")) is False


def test_nonexistent_path_must_exist(sandbox_env: dict[str, Path]) -> None:
    sandbox_root = sandbox_env["sandbox_root"]

    with pytest.raises(InvalidPathError):
        resolve_sandbox_path(sandbox_root, "src/nonexistent_file.py", must_exist=True)

    # Allowed when must_exist=False (e.g. for creating new files)
    resolved = resolve_sandbox_path(sandbox_root, "src/new_file.py", must_exist=False)
    assert resolved == (sandbox_root / "src" / "new_file.py").resolve()
