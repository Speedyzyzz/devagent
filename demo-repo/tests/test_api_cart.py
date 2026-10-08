"""Tests for cart API endpoint behavior."""
from backend.app.api.cart import create_cart_endpoint


def test_create_cart_returns_201_created():
    response = create_cart_endpoint("usr_999")
    assert response["status_code"] == 201
    assert response["cart_id"] == "cart_usr_999"
    assert response["items"] == []
