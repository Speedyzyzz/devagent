"""Server-Sent Events streaming endpoint for real-time agent telemetry."""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from backend.app.api.dependencies import get_database, get_manager
from backend.app.sessions.manager import SessionManager
from backend.app.storage.database import Database

router = APIRouter(prefix="/stream", tags=["Streaming"])


@router.get("/{session_id}")
async def stream_session_events(
    session_id: str,
    request: Request,
    manager: SessionManager = Depends(get_manager),
    db: Database = Depends(get_database),
) -> EventSourceResponse:
    """Stream real-time agent execution events to clients using Server-Sent Events."""

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        # 1. Replay past events from database (for reconnecting clients)
        past_events = db.get_events(session_id)
        for pe in past_events:
            yield {
                "event": pe["type"],
                "data": json.dumps({
                    "type": pe["type"],
                    "session_id": session_id,
                    "step": pe["step"],
                    "timestamp": pe["created_at"],
                    "data": pe["data"],
                }),
            }

        # 2. Check if session already ended
        session_info = db.get_session(session_id)
        if session_info and session_info["status"] in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"):
            return

        # 3. Stream live incoming events from queue
        queue = manager.get_event_queue(session_id)
        try:
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Keep-alive ping
                    yield {"event": "ping", "data": "{}"}
                    continue

                if event is None:
                    # Stream complete
                    break

                yield {
                    "event": event.type.value,
                    "data": json.dumps({
                        "type": event.type.value,
                        "session_id": event.session_id,
                        "step": event.step,
                        "timestamp": event.timestamp,
                        "data": event.data,
                    }),
                }
        finally:
            manager.unsubscribe_queue(session_id, queue)

    return EventSourceResponse(event_generator())
