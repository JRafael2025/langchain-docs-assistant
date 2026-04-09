"""
Database connection management — pool setup, session factory, retry logic.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from database.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/appdb")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def create_db_engine():
    """
    Create a SQLAlchemy engine with connection pooling configured.

    Uses QueuePool with settings from environment variables. Enables
    pool pre-ping to detect stale connections before use.

    Returns:
        Configured SQLAlchemy Engine instance.
    """
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_pre_ping=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()

    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session with automatic
    commit on success and rollback on exception.

    Usage:
        with get_db_session() as session:
            user = session.query(User).filter_by(email=email).first()

    Yields:
        SQLAlchemy Session object.

    Raises:
        Any exception from the wrapped code (after rolling back).
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def execute_with_retry(query_func, retries: int = MAX_RETRIES) -> any:
    """
    Execute a database operation with automatic retry on connection errors.

    Args:
        query_func: A callable that accepts a Session and performs DB work.
        retries: Number of retry attempts before raising the final error.

    Returns:
        Return value of query_func.

    Raises:
        OperationalError: If all retry attempts are exhausted.

    Example:
        result = execute_with_retry(lambda s: s.query(User).count())
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with get_db_session() as session:
                return query_func(session)
        except OperationalError as e:
            last_error = e
            logger.warning(
                "DB connection error on attempt %d/%d: %s", attempt, retries, e
            )
            if attempt < retries:
                time.sleep(RETRY_DELAY_SECONDS * attempt)  # exponential backoff

    raise OperationalError(
        f"Database operation failed after {retries} attempts."
    ) from last_error


def check_db_health() -> bool:
    """
    Ping the database to verify connectivity.

    Returns:
        True if the database responds, False otherwise.
    """
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return False


def init_db():
    """
    Create all tables defined in models.py if they do not exist.
    Should be called once at application startup.
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")
