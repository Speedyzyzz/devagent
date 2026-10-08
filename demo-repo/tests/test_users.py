"""Tests for user profile formatting and null handling."""
from backend.app.users.service import UserProfile, format_user_header


def test_format_user_header_with_name():
    user = UserProfile(user_id="u123", display_name="alice")
    header = format_user_header(user)
    assert header == "USER: ALICE"


def test_format_user_header_with_null_name():
    """Verify null display name gracefully falls back to ANONYMOUS instead of crashing."""
    user = UserProfile(user_id="u456", display_name=None)
    header = format_user_header(user)
    assert header == "USER: ANONYMOUS"
