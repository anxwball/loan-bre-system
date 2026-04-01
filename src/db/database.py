"""Provide SQLAlchemy Core database bootstrap utilities for Phase 4b.

This module owns engine construction and schema initialization for the
persistence layer introduced in Phase 4b. It is intentionally limited to
connection and transaction helpers for SQLAlchemy Core; repository logic lives
under `src/db/repositories/`.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Connection, Engine, create_engine, event

from src.db.schema import metadata

DEFAULT_SQLITE_PATH = Path("data/audit/loan_bre_system.db")
DATABASE_URL_ENV = "LOAN_BRE_DATABASE_URL"


def build_sqlite_url(database_path: Path | str = DEFAULT_SQLITE_PATH) -> str:
    """Build a SQLite URL from a local filesystem path.

    Args:
        database_path: Target SQLite database file path.

    Returns:
        SQLAlchemy-compatible SQLite URL.
    """

    resolved_path = Path(database_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{resolved_path.as_posix()}"


def resolve_database_url(database_url: str | None = None) -> str:
    """Resolve database URL from explicit input, env var, or SQLite fallback.

    Args:
        database_url: Optional explicit SQLAlchemy database URL.

    Returns:
        Effective database URL for engine creation.
    """

    if database_url:
        return database_url

    env_database_url = os.getenv(DATABASE_URL_ENV)
    if env_database_url:
        return env_database_url

    return build_sqlite_url()


def create_db_engine(database_url: str | None = None, echo: bool = False) -> Engine:
    """Create a SQLAlchemy Core engine for the configured persistence backend.

    Args:
        database_url: Optional explicit SQLAlchemy URL.
        echo: Whether SQLAlchemy should echo generated SQL.

    Returns:
        Configured SQLAlchemy engine.
    """

    engine = create_engine(resolve_database_url(database_url), echo=echo)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def initialize_database(engine: Engine) -> None:
    """Create all configured tables in the target database.

    Args:
        engine: SQLAlchemy engine connected to target database.

    Returns:
        None.
    """

    metadata.create_all(engine)


@contextmanager
def begin_connection(engine: Engine) -> Iterator[Connection]:
    """Yield a transactional connection using SQLAlchemy Core semantics.

    Args:
        engine: SQLAlchemy engine used to open the transaction.

    Returns:
        Iterator that yields one transactional Connection.
    """

    with engine.begin() as connection:
        yield connection


def dispose_engine(engine: Engine) -> None:
    """Dispose pooled connections associated with a SQLAlchemy engine.

    Args:
        engine: SQLAlchemy engine to dispose.

    Returns:
        None.
    """

    engine.dispose()


__all__ = [
    "DEFAULT_SQLITE_PATH",
    "DATABASE_URL_ENV",
    "build_sqlite_url",
    "resolve_database_url",
    "create_db_engine",
    "initialize_database",
    "begin_connection",
    "dispose_engine",
]
