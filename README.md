# DevAgent

> **A policy-constrained autonomous software-engineering runtime that gives an LLM controlled access to a repository through deterministic filesystem, search, patch, and verification tools.**

[![Tests](https://img.shields.io/badge/Tests-33%20passed-emerald)](backend/tests)
[![Benchmark Resolution](https://img.shields.io/badge/Benchmark-100%25%20Resolved-blue)](evaluation/benchmark_report.md)
[![Security Perimeter](https://img.shields.io/badge/Sandbox-100%25%20Exploits%20Blocked-green)](backend/tests/test_security.py)
[![License](https://img.shields.io/badge/License-MIT-zinc)](LICENSE)

---

## 1. What DevAgent Actually Is

DevAgent is **not** a conversational chatbot that emits raw code blocks. It is an **execution system** where an LLM controls a restricted set of deterministic engineering tools:

```text
Understand repository
        ↓
Explore filesystem
        ↓
Search relevant code
        ↓
Read targeted context
        ↓
Form hypothesis
        ↓
Modify code (Atomic + AST Syntax Check)
        ↓
Run verification (pytest / npm)
        ↓
Inspect failure (Self-correction)
        ↓
Correct implementation
        ↓
Generate unified diff
        ↓
Generate root-cause analysis (RCA) report
```

### The Core Design Principle
- **The LLM decides**: *"What should I investigate next?"*
- **The runtime tools decide**: *"Is that operation allowed, canonical, sandboxed, and syntax-valid?"*

---

## 2. Empirical Benchmark Evaluation

DevAgent was rigorously evaluated against a standardized 5-bug benchmark repository spanning authentication, business logic, pagination slices, null handling, and HTTP status handling:

| Case ID | Benchmark Issue | Status | Turns | Tools | Patch | Runtime |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `case_001_guest_session` | Guest Checkout Session Expiry 401 | **PASSED** | 6 | 5 | 2 lines | 0.12s |
| `case_002_cart_tax` | Cart Total Tax Calculation Omission | **PASSED** | 6 | 5 | 5 lines | 0.13s |
| `case_003_catalog_pagination` | Catalog Pagination Off-By-One Truncation | **PASSED** | 6 | 5 | 3 lines | 0.12s |
| `case_004_user_null_name` | User Null Display Name AttributeError | **PASSED** | 6 | 5 | 4 lines | 0.13s |
| `case_005_cart_creation_status` | Cart Creation Endpoint 404 Status Bug | **PASSED** | 6 | 5 | 2 lines | 0.13s |

### Verified Summary Metrics
- **Verified Resolution Rate**: **`100.0%`** (5 / 5 benchmark cases resolved & verified)
- **Average Turns to Resolution**: **`6.0`** (out of 8 turn budget)
- **Average Tool Calls per Task**: **`5.0`** calls
- **Average Verification Runs**: **`1.0`** runs
- **Average Patch Size**: **`3.2`** lines changed
- **Security Traversal Block Rate**: **`100.0%`** (8 / 8 path traversal and symlink exploits blocked)

---

## 3. Architecture

```text
                              USER
                                │
                                ▼
                    ┌─────────────────────┐
                    │  NEXT.JS 15 UI      │
                    │                     │
                    │ Issue Input         │
                    │ Agent Timeline      │
                    │ Diff Viewer         │
                    │ RCA Report          │
                    └──────────┬──────────┘
                               │
                          HTTP + SSE
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FASTAPI        │
                    │                     │
                    │ Session API         │
                    │ Stream API (SSE)    │
                    │ Cancellation        │
                    └──────────┬──────────┘
                               │
                               ▼
                  ┌───────────────────────────┐
                  │       AGENT ENGINE        │
                  │                           │
                  │ State & Budgets           │
                  │ Phase transitions         │
                  │ LLM provider abstraction  │
                  └─────────────┬─────────────┘
                                │
                          Tool Registry
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
       FILESYSTEM            SEARCH              PATCH
       TOOL                  TOOL                TOOL
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                                ▼
                         VERIFICATION
                             TOOL
                                │
                                ▼
                     ┌─────────────────────┐
                     │  SANDBOX WORKSPACE  │
                     │                     │
                     │ repo/               │
                     │ tests/              │
                     │ temporary files     │
                     └─────────────────────┘
                                │
                                ▼
                       VERIFIED RESULT
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                 DIFF                  RCA REPORT
```

---

## 4. Security Sandbox Perimeter

1. **Path Resolution & Containment**: Every requested path is resolved with `Path.resolve(strict=False)` and checked against `sandbox_root.resolve()`. Any path outside raises `SandboxViolation`.
2. **Symlink Escape Protection**: Symlinks pointing outside the sandbox root are detected and blocked.
3. **Sensitive File Default-Deny**: Inflexible block on `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `credentials.json`, and `.git/config`.
4. **Zero Arbitrary Shell Access**: No generic shell tool (`bash`/`sh`) is exposed. Only strict structured verification runners (`pytest`, `npm test`) are executed via `asyncio.create_subprocess_exec` (`shell=False`).
5. **Atomic Writes & AST Validation**: Patches are written to temporary files, checked with Python AST compilation (`ast.parse`), and atomically renamed with `os.replace`.

---

## 5. Deterministic Tool Set

1. **`list_directory`**: Explores directory structure up to depth 2 with automatic filtering of `.git`, `.env`, and dependencies.
2. **`search_code`**: Fast keyword and regex search with extension filters, binary exclusion, and 15 match ceilings. Supports `ripgrep` with pure Python fallback.
3. **`read_file_lines`**: Inspects targeted line slices (up to 150 lines) with numbered references (`35 | ...`).
4. **`apply_patch`**: Exact-match search/replace block patching. Ambiguous (>1) or missing (0) matches are rejected. Pre-write AST syntax validation.
5. **`execute_verification`**: Sandboxed test execution with 60s timeout and 20,000 character output limit.

---

## 6. Quickstart Guide

### Prerequisites
- Python 3.11+ (tested on Python 3.13)
- Node.js 18+ (tested on Node.js 22 & 26)

### 1. Clone & Set Up Backend

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Run complete test suite (33 tests)
pytest backend/tests/ -v

# Run benchmark suite across all 5 cases
python -m evaluation.runner
```

### 2. Start the Backend API

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI backend will be live at `http://localhost:8000`. OpenAPI docs are available at `http://localhost:8000/docs`.

### 3. Start the Next.js Mission Control Frontend

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` to launch the DevAgent Mission Control dashboard.

### 4. Running via Docker Compose

```bash
docker-compose up --build
```

---

## 7. Documentation

- [System Architecture](docs/architecture.md)
- [Security & Threat Model](docs/security.md)
- [Agent Execution Loop & Lifecycle](docs/agent-loop.md)
- [Tool Contracts & Result Envelopes](docs/tool-contracts.md)
- [Benchmark Evaluation Suite](docs/evaluation.md)

---

## 8. License

MIT License. See [LICENSE](LICENSE) for details.
