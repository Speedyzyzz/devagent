"""Tests for authentication and session recovery."""
from backend.app.auth.session import validate_guest_session


def test_valid_guest_session():
    session = validate_guest_session("active_token_123", is_expired=False)
    assert session["session_id"] == "active_token_123"
    assert session["role"] == "guest"


def test_expired_guest_session_recovers_anonymously():
    """Verify expired guest sessions smoothly recover to anonymous sessions instead of raising 401."""
    session = validate_guest_session("expired_token_456", is_expired=True)
    assert session is not None
    assert session["role"] == "anonymous"
    assert session["is_guest"] is True
