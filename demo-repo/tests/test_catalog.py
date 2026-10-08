"""Tests for catalog pagination."""
from backend.app.catalog.paginator import paginate_items


def test_paginate_first_page_full_size():
    items = list(range(10))
    result = paginate_items(items, page=1, page_size=5)
    assert len(result) == 5
    assert result == [0, 1, 2, 3, 4]


def test_paginate_second_page():
    items = list(range(10))
    result = paginate_items(items, page=2, page_size=5)
    assert len(result) == 5
    assert result == [5, 6, 7, 8, 9]
