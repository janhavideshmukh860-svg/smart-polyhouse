"""
Centralized logging configuration.

Provides a single `configure_logging()` entrypoint (called once at app
startup) and a `get_logger(name)` helper used throughout the codebase.

Security note: this module and its callers must NEVER log secrets
(passwords, JWT secret keys, database credentials, raw tokens). Redaction
helpers are provided for any place that might otherwise be tempted to log
a full settings/config object.
"""
from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from app.core.config import settings

_CONFIGURED = False

# Keys that must never appear in logs even if a dict is logged accidentally.
_SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "jwt_secret_key",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "database_url",
    "authorization",
}


def redact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy of `data` with sensitive values masked."""
    redacted = {}
    for k, v in data.items():
        if k.lower() in _SENSITIVE_KEYS:
            redacted[k] = "***REDACTED***"
        else:
            redacted[k] = v
    return redacted


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_JSON:
        fmt = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on reload
    root.handlers = [handler]

    # Quiet down noisy third-party loggers a bit unless DEBUG
    if level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
