# DevAgent — Tool Contracts & Result Envelopes

Every tool invocation adheres to a typed contract governed by Pydantic v2 schemas.

## Standard Response Contract (`ToolResult`)

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": { ... }
}
```

On failure:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PATCH_AMBIGUOUS",
    "message": "Target block appears 2 times.",
    "details": { "occurrences": 2 }
  },
  "metadata": {}
}
```

---

## 1. `list_directory`
- **Purpose**: Workspace orientation and file tree mapping.
- **Input**:
  - `path`: string (default: `"."`)
- **Limits**: Maximum depth 2, maximum 200 entries.
- **Filters**: Excludes `.git`, `.env`, `node_modules`, `__pycache__`, `.venv`, and sensitive credential paths.

---

## 2. `search_code`
- **Purpose**: Fast lexical keyword and regex searching.
- **Input**:
  - `query`: string (search term or regex pattern)
  - `extension`: string | null (e.g. `".py"`)
  - `path`: string (default: `"."`)
- **Limits**: Maximum 15 matches, 200 character previews per line.
- **Dual Engine**: Uses `ripgrep` (`rg`) when installed on host; falls back to pure Python regex engine with identical exclusion rules and binary file skipping.

---

## 3. `read_file_lines`
- **Purpose**: Targeted reading of candidate source code slices.
- **Input**:
  - `path`: string
  - `start_line`: int (1-indexed, >= 1)
  - `end_line`: int (inclusive, >= `start_line`)
- **Limits**: Maximum range: 150 lines. Line numbers formatted as `35 | ...`.

---

## 4. `apply_patch`
- **Purpose**: Exact-match atomic block replacement with syntax checking.
- **Input**:
  - `path`: string
  - `search_block`: string (exact lines to find)
  - `replace_block`: string (exact lines to insert)
- **Rules**:
  - Occurrences == 0 -> `PATCH_NOT_FOUND`
  - Occurrences > 1 -> `PATCH_AMBIGUOUS` (fails immediately, returning occurrences count)
  - Pre-write validation: Python AST compilation (`ast.parse`)
  - Output: unified diff formatted string.

---

## 5. `execute_verification`
- **Purpose**: Run test suites against the modified workspace.
- **Input**:
  - `runner`: string (`pytest`, `python -m pytest`, `npm test`)
  - `args`: list of strings (e.g. `["tests/test_auth.py"]`)
  - `cwd`: string (default: `"."`)
- **Limits**: 60-second execution timeout, 20,000 character output limit.
