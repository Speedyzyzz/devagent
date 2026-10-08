"""Cart calculation services."""


def calculate_cart_total(subtotal: float, discount: float, tax_rate: float = 0.10) -> float:
    """
    Calculate final cart total including discounts and applicable tax.
    BUG: Tax is currently omitted from final total computation.
    """
    # BUGGY IMPLEMENTATION: tax is omitted
    total = subtotal - discount
    return round(total, 2)
