# Demo Repository (E-Commerce Service)

This repository contains intentional bugs designed for evaluating autonomous software engineering agents.

## Known Issues

1. **Auth**: Expired guest session raises HTTP 401 instead of falling back to anonymous session (`backend/app/auth/session.py`).
2. **Cart Calculation**: Cart total omits tax calculation (`backend/app/cart/service.py`).
3. **Catalog Pagination**: Off-by-one error truncates last item in page slice (`backend/app/catalog/paginator.py`).
4. **User Profile**: `AttributeError` when formatting display name if null (`backend/app/users/service.py`).
5. **Cart API**: POST `/cart` incorrectly returns status 404 instead of 201 (`backend/app/api/cart.py`).

## Running Tests

```bash
PYTHONPATH=. pytest tests/
```
