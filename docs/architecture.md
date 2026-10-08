# DevAgent — System Architecture

## Overview

DevAgent is a policy-constrained, autonomous software-engineering execution runtime. Unlike chatbot code generators that dump conversational code suggestions, DevAgent couples an LLM with a deterministic tool registry operating strictly inside an isolated workspace.

```
                         ┌─────────────────────┐
                         │       USER          │
                         │ Repo + Issue        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Next.js 15 UI     │
                         │ Mission Control     │
                         │ SSE Real-time Bus   │
                         └──────────┬──────────┘
                                    │
                               HTTP / SSE
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI API      │
                         │ Session Management  │
                         │ SSE Event Bus       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────┐
                 │         Agent Runtime            │
                 │                                  │
                 │ ┌──────────────────────────────┐ │
                 │ │       Agent Engine           │ │
                 │ └──────────────┬───────────────┘ │
                 │                │                 │
                 │      Budget & Security Policy    │
                 │                │                 │
                 │ ┌──────────────┼───────────────┐ │
                 │ ▼              ▼               ▼ │
                 │ FS           Search          Patch│
                 │ Tool         Tool             Tool│
                 │ └──────────────┬───────────────┘ │
                 │                │                 │
                 │          Verification            │
                 │                │                 │
                 └────────────────┼─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────────┐
                         │  Sandbox Workspace  │
                         │                     │
                         │ repo/               │
                         │ tests/              │
                         │ temporary files     │
                         └─────────────────────┘
```

## Layers of Separation

1. **API Layer (`backend/app/api`)**:
   - Manages HTTP REST requests and SSE event streams.
   - Decoupled from execution mechanics through dependency injection.

2. **Session Layer (`backend/app/sessions`)**:
   - Allocates dedicated disk workspaces per session: `sandboxes/sessions/{session_id}/repo`.
   - Manages asynchronous background tasks and cancellation signals.

3. **Agent Runtime (`backend/app/agent`)**:
   - `AgentEngine`: Enforces phase transitions, turn limits, tool call limits, test attempt limits, and wall-clock timeouts.
   - `LLMProvider`: Protocol abstraction supporting Gemini, OpenAI, and deterministic Mock providers.

4. **Security & Tool Registry (`backend/app/agent/tools` & `backend/app/core/security.py`)**:
   - Validates all input schemas via Pydantic v2.
   - Intercepts and canonicalizes all filesystem paths, preventing traversal or symlink escapes.
   - Returns structured `ToolResult` envelopes with zero leakage of raw system exceptions.

5. **Sandbox Workspace (`sandboxes/`)**:
   - Each session runs against an isolated copy of the repository.
   - Never shares state between concurrent sessions.
