"""Health check endpoint."""
from fastapi import APIRouter
from backend.app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "DevAgent API",
        "provider": settings.llm_provider,
    }
