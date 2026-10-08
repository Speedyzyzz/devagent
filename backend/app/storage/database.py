"""SQLite storage repository for DevAgent sessions and telemetry events."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from backend.app.core.config import get_settings


class Database:
    """Lightweight SQLite database for persistent session records."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            settings = get_settings()
            db_dir = settings.sandbox_root.parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "devagent.db"
        else:
            self.db_path = db_path

        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                repository TEXT NOT NULL,
                issue TEXT NOT NULL,
                status TEXT NOT NULL,
                iteration INTEGER DEFAULT 0,
                files_changed TEXT DEFAULT '[]',
                root_cause TEXT,
                final_diff TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                started_at REAL,
                completed_at REAL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                step INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS patches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                diff TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS verification_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                runner TEXT NOT NULL,
                args TEXT NOT NULL,
                exit_code INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                stdout TEXT,
                stderr TEXT,
                duration REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
            CREATE INDEX IF NOT EXISTS idx_patches_session ON patches(session_id);
            CREATE INDEX IF NOT EXISTS idx_verifications_session ON verification_runs(session_id);
            """)

    def create_session(self, session_id: str, repository: str, issue: str, status: str = "CREATED") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, repository, issue, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, repository, issue, status, now),
            )

    def update_session(
        self,
        session_id: str,
        status: str,
        iteration: int,
        files_changed: list[str],
        root_cause: str | None = None,
        final_diff: str | None = None,
        error: str | None = None,
        started_at: float | None = None,
        completed_at: float | None = None,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET status = ?, iteration = ?, files_changed = ?, root_cause = ?, final_diff = ?,
                    error = ?, started_at = coalesce(?, started_at), completed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    iteration,
                    json.dumps(files_changed),
                    root_cause,
                    final_diff,
                    error,
                    started_at,
                    completed_at,
                    session_id,
                ),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["files_changed"] = json.loads(data["files_changed"] or "[]")
            return data

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["files_changed"] = json.loads(item["files_changed"] or "[]")
                results.append(item)
            return results

    def add_event(self, session_id: str, event_type: str, step: int, payload: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO events (session_id, type, step, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, event_type, step, json.dumps(payload), now),
            )

    def get_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["data"] = json.loads(item["payload"])
                results.append(item)
            return results


_default_db: Database | None = None


def get_db() -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db
