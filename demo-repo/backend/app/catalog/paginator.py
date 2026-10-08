"""Catalog pagination utilities."""
from typing import Any


def paginate_items(items: list[Any], page: int = 1, page_size: int = 10) -> list[Any]:
    """
    Return a page slice of items.
    BUG: Off-by-one error drops the final element of each page.
    """
    start = (page - 1) * page_size
    # BUG: subtracting 1 truncates the last element in slice notation
    end = (page * page_size) - 1
    return items[start:end]
