"""Main FastAPI application entry point for DevAgent."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import health, sessions, stream
from backend.app.core.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.storage.database import get_db

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    settings = get_settings()
    settings.sandbox_root.mkdir(parents=True, exist_ok=True)
    get_db()
    logger.info("DevAgent runtime initialized successfully")
    yield
    logger.info("DevAgent runtime shutting down")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="DevAgent API",
        description="Policy-constrained autonomous software-engineering execution runtime.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Enable CORS for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API v1 routes
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(stream.router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
