"""Cart API endpoints."""
from typing import Any


def create_cart_endpoint(user_id: str) -> dict[str, Any]:
    """
    Create a new shopping cart for a user.
    BUG: Incorrectly returns HTTP 404 instead of HTTP 201 Created.
    """
    return {
        "status_code": 404,  # BUG: Should be 201
        "cart_id": f"cart_{user_id}",
        "items": [],
    }
