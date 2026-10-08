"""Session management API routes."""
from pathlib import Path
from typing import Any
import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.dependencies import get_manager
from backend.app.core.exceptions import SessionNotFoundError
from backend.app.sessions.manager import SessionManager

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class CreateSessionRequest(BaseModel):
    issue: str = Field(..., description="Bug description or issue specification")
    repository: str = Field(default="demo-repo", description="Target repository name")
    verification_instruction: str | None = Field(default=None, description="Optional custom test command")
    provider: str | None = Field(default=None, description="LLM provider: 'mock', 'gemini', 'openai'")
    case_id: str | None = Field(default=None, description="Optional benchmark case ID to load")


class CreateSessionResponse(BaseModel):
    session_id: str
    status: str


@router.post("", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    manager: SessionManager = Depends(get_manager),
) -> CreateSessionResponse:
    session_id = await manager.create_session(
        issue=request.issue,
        repository=request.repository,
        verification_instruction=request.verification_instruction,
        provider_name=request.provider,
        case_id=request.case_id,
    )
    return CreateSessionResponse(session_id=session_id, status="CREATED")


@router.get("")
async def list_sessions(manager: SessionManager = Depends(get_manager)) -> list[dict[str, Any]]:
    return manager.db.list_sessions()


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_manager),
) -> dict[str, Any]:
    try:
        return manager.get_session_state(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@router.post("/{session_id}/cancel")
async def cancel_session(
    session_id: str,
    manager: SessionManager = Depends(get_manager),
) -> dict[str, Any]:
    try:
        manager.cancel_session(session_id)
        return {"session_id": session_id, "status": "CANCELLATION_REQUESTED"}
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@router.get("/cases/benchmarks")
async def get_benchmark_cases() -> list[dict[str, Any]]:
    """Return available benchmark test cases for UI quick-selection."""
    cases_dir = Path("./evaluation/cases")
    cases: list[dict[str, Any]] = []
    if cases_dir.exists():
        for f in sorted(cases_dir.glob("*.yaml")):
            with open(f, "r", encoding="utf-8") as yf:
                data = yaml.safe_load(yf)
                cases.append({
                    "id": data["id"],
                    "name": data["name"],
                    "issue": data["issue"].strip(),
                    "verification": data.get("verification", {}),
                    "expected_files": data.get("expected_files", []),
                })
    return cases
