# DevAgent — Autonomous Execution Loop & Phase Transitions

## Lifecycle State Machine

```
CREATED
   ↓
INITIALIZING
   ↓
RECONNAISSANCE ───► (list_directory)
   ↓
INVESTIGATION  ───► (search_code, read_file_lines)
   ↓
PATCHING       ───► (apply_patch)
   ↓
VERIFYING      ───► (execute_verification)
   ↓
   ├── PASS ──► Check completion criteria ──► COMPLETED
   │
   └── FAIL ──► CORRECTING ──► INVESTIGATION ──► ...
                                     │
                             (Budget Exceeded)
                                     │
                                     ▼
                                  FAILED
```

## Budget Constraints

Every session is constrained by four strict upper limits:
- **`MAX_ITERATIONS`**: 8 turns.
- **`MAX_TOOL_CALLS`**: 20 total tool executions.
- **`MAX_VERIFICATION_ATTEMPTS`**: 5 test suite runs.
- **`MAX_RUNTIME_SECONDS`**: 300 seconds wall-clock time.

If any limit is breached, the runtime terminates the session immediately with status `FAILED` or `TIMEOUT`.

## Completion Gating

The agent cannot declare itself finished based on its own belief. The `AgentEngine` enforces three mandatory gates:
1. At least one file has been modified (`len(files_changed) > 0`).
2. Verification has been executed (`len(verification_runs) > 0`).
3. The latest verification run passed (`last_verification_passed() == True`).

If an LLM attempts to signal completion before satisfying these requirements, the runtime rejects the claim and instructs the model to continue investigating.
