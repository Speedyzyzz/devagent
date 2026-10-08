"""User profile and formatting service."""


class UserProfile:
    def __init__(self, user_id: str, display_name: str | None = None) -> None:
        self.user_id = user_id
        self.display_name = display_name


def format_user_header(user: UserProfile) -> str:
    """
    Format a banner header for a user.
    BUG: Crashes with AttributeError when user.display_name is None.
    """
    # BUGGY: Assumes display_name is always non-null string
    return f"USER: {user.display_name.upper()}"
