"""Shared pytest fixtures for DevAgent tests."""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator
import pytest


@pytest.fixture
def sandbox_env() -> Generator[dict[str, Path], None, None]:
    """
    Creates an isolated sandbox environment with:
    - inside safe files & dirs
    - sensitive files (.env, .git/config)
    - external directory with secret files
    - symlink inside sandbox pointing to outside secret file
    """
    outside_dir = Path(tempfile.mkdtemp(prefix="devagent_outside_"))
    outside_secret = outside_dir / "secret.txt"
    outside_secret.write_text("SUPER_SECRET_EXTERNAL_KEY")

    sandbox_dir = Path(tempfile.mkdtemp(prefix="devagent_sandbox_"))

    # Populate safe files
    (sandbox_dir / "README.md").write_text("# Demo Workspace")
    src_dir = sandbox_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "main.py").write_text("print('hello world')\n")
    (src_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n")

    # Populate sensitive files
    (sandbox_dir / ".env").write_text("SECRET_TOKEN=12345")
    (sandbox_dir / ".env.local").write_text("LOCAL_SECRET=abcde")
    git_dir = sandbox_dir / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)
    (git_dir / "config").write_text("[core]\nrepositoryformatversion = 0")

    # Symlink pointing outside sandbox
    escape_symlink = sandbox_dir / "escape_link"
    try:
        escape_symlink.symlink_to(outside_secret)
    except OSError:
        pass  # On systems where symlinks require privileges

    # Safe internal symlink
    safe_symlink = sandbox_dir / "safe_link"
    try:
        safe_symlink.symlink_to(sandbox_dir / "README.md")
    except OSError:
        pass

    yield {
        "sandbox_root": sandbox_dir,
        "outside_dir": outside_dir,
        "outside_secret": outside_secret,
        "escape_symlink": escape_symlink,
        "safe_symlink": safe_symlink,
    }

    # Cleanup
    shutil.rmtree(sandbox_dir, ignore_errors=True)
    shutil.rmtree(outside_dir, ignore_errors=True)
