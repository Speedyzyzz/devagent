"""Auth session management for guest and registered users."""
from typing import Any


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def create_anonymous_session() -> dict[str, Any]:
    """Create a new anonymous guest session token."""
    return {
        "session_id": "anon_guest_new",
        "is_guest": True,
        "is_expired": False,
        "role": "anonymous",
    }


def validate_guest_session(token: str, is_expired: bool = False) -> dict[str, Any]:
    """
    Validate an incoming guest session.
    BUG: If the guest session is expired, it incorrectly raises HTTP 401 instead of
    falling back to create_anonymous_session() to allow seamless cart recovery.
    """
    if is_expired:
        raise HTTPException(status_code=401, detail="Guest session expired")

    return {
        "session_id": token,
        "is_guest": True,
        "is_expired": False,
        "role": "guest",
    }
