"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "DevAgent API"


@pytest.mark.asyncio
async def test_benchmark_cases_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/cases/benchmarks")
        assert resp.status_code == 200
        cases = resp.json()
        assert len(cases) == 5
        case_ids = [c["id"] for c in cases]
        assert "case_001_guest_session" in case_ids
        assert "case_002_cart_tax" in case_ids


@pytest.mark.asyncio
async def test_session_lifecycle_api() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session with benchmark case 1
        create_resp = await client.post(
            "/api/v1/sessions",
            json={
                "issue": "Fix guest checkout 401 bug",
                "repository": "demo-repo",
                "case_id": "case_001_guest_session",
            },
        )
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]
        assert session_id.startswith("sess_")

        # Fetch session
        get_resp = await client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 200
        session_data = get_resp.json()
        assert session_data["session_id"] == session_id

        # Cancel session
        cancel_resp = await client.post(f"/api/v1/sessions/{session_id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "CANCELLATION_REQUESTED"


@pytest.mark.asyncio
async def test_nonexistent_session_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/sessions/nonexistent_xyz")
        assert resp.status_code == 404
