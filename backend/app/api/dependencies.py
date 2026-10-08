"""Dependency injection providers for FastAPI routes."""
from backend.app.core.config import Settings, get_settings
from backend.app.sessions.manager import SessionManager, get_session_manager
from backend.app.storage.database import Database, get_db


def get_app_settings() -> Settings:
    return get_settings()


def get_manager() -> SessionManager:
    return get_session_manager()


def get_database() -> Database:
    return get_db()
