"""Tests for cart total calculation."""
from backend.app.cart.service import calculate_cart_total


def test_calculate_cart_total_with_tax():
    # 100 subtotal - 20 discount = 80 net. 10% tax on net = 8 tax. Total should be 88.0
    total = calculate_cart_total(subtotal=100.0, discount=20.0, tax_rate=0.10)
    assert total == 88.0


def test_calculate_cart_total_zero_discount():
    # 50 subtotal - 0 discount = 50 net. 10% tax = 5 tax. Total should be 55.0
    total = calculate_cart_total(subtotal=50.0, discount=0.0, tax_rate=0.10)
    assert total == 55.0
