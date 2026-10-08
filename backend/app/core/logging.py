"""Structured logging with redaction for DevAgent."""
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

# Sensitive patterns to scrub from log messages
SENSITIVE_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[:=]\s*)[^\s,;&'\"]+", re.IGNORECASE),
    re.compile(r"(token\s*[:=]\s*)[^\s,;&'\"]+", re.IGNORECASE),
    re.compile(r"(secret\s*[:=]\s*)[^\s,;&'\"]+", re.IGNORECASE),
    re.compile(r"(password\s*[:=]\s*)[^\s,;&'\"]+", re.IGNORECASE),
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
]


def redact_sensitive(text: str) -> str:
    """Scrub potential credentials from logged text."""
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON with redacted contents."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
        }

        # Include custom structured attributes if provided
        for attr in ("session_id", "event", "tool", "duration_ms", "step", "iteration"):
            if hasattr(record, attr):
                log_payload[attr] = getattr(record, attr)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def get_logger(name: str = "devagent") -> logging.Logger:
    """Retrieve configured logger with JSON formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
