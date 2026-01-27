"""Schema versioning and migration system."""

import sqlite3
from pathlib import Path

from jot.db.connection import CURRENT_SCHEMA_VERSION, get_connection
from jot.db.exceptions import DatabaseError


def get_schema_version(conn: sqlite3.Connection | None = None) -> int:
    """Get current database schema version.

    Args:
        conn: Database connection (creates new if None).

    Returns:
        int: Current schema version (0 if no schema exists).

    Raises:
        DatabaseError: If version cannot be determined.
    """
    if conn is None:
        conn = get_connection()
        close_after = True
    else:
        close_after = False

    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        result = cursor.fetchone()
        if result is None:
            raise DatabaseError("Cannot get schema version: no result from PRAGMA user_version")
        version: int = result[0]
        return version
    except sqlite3.Error as e:
        raise DatabaseError(f"Cannot get schema version: {e}") from e
    finally:
        if close_after:
            conn.close()


def migrate_schema(conn: sqlite3.Connection | None = None) -> None:
    """Migrate database schema to current version.

    Checks current schema version and applies necessary migrations.
    Idempotent: safe to call multiple times.

    Args:
        conn: Database connection (creates new if None).

    Raises:
        DatabaseError: If migration fails.
    """
    if conn is None:
        conn = get_connection()
        close_after = True
    else:
        close_after = False

    try:
        # Get version using the provided connection (don't create new one)
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]

        if current_version < CURRENT_SCHEMA_VERSION:
            # Apply migrations in order
            if current_version < 1:
                _migrate_to_version_1(conn)
                current_version = 1

            # Set schema version after migrations
            cursor.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
            conn.commit()

    except sqlite3.Error as e:
        raise DatabaseError(f"Migration failed: {e}") from e
    finally:
        if close_after:
            conn.close()


def _migrate_to_version_1(conn: sqlite3.Connection) -> None:
    """Migrate database from version 0 to version 1.

    Creates initial schema with tasks and task_events tables.

    Args:
        conn: Database connection.

    Raises:
        DatabaseError: If migration fails.
    """
    # Read schema.sql and execute
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()

    try:
        conn.executescript(schema_sql)
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to create schema: {e}") from e
