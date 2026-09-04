"""
Database connection layer.

- SQLAlchemy 2.x engine with connection pooling.
- Environment-based configuration (see app.core.config.Settings).
- The app is allowed to START even if the database is unreachable
  (controlled by ALLOW_START_WITHOUT_DB) so that local ML experimentation
  and non-DB endpoints keep working; DB-dependent endpoints will report a
  clear 503 error in that case instead of crashing the whole process.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""
    pass


def _build_engine():
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        future=True,
    )


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

_db_available: bool | None = None  # cached last known status


def check_database_connection() -> bool:
    """Attempt a lightweight connection check. Returns True/False and
    caches the result for the status endpoint."""
    global _db_available
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_available = True
        return True
    except SQLAlchemyError as exc:
        logger.warning("Database connectivity check failed: %s", exc.__class__.__name__)
        _db_available = False
        return False


def get_last_known_db_status() -> bool | None:
    return _db_available


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for scripts / services that need a session outside
    of a FastAPI request (e.g. training scripts writing to model_registry)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
