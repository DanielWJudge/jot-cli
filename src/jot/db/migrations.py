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

            if current_version < 2:
                _migrate_to_version_2(conn)
                current_version = 2

            if current_version < 3:
                _migrate_to_version_3(conn)
                current_version = 3

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


def _migrate_to_version_2(conn: sqlite3.Connection) -> None:
    """Migrate database from version 1 to version 2.

    Adds cancelled_at and cancel_reason columns to tasks table.

    Args:
        conn: Database connection.

    Raises:
        DatabaseError: If migration fails.
    """
    try:
        cursor = conn.cursor()

        # Check if columns already exist (for idempotency)
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Add cancelled_at column (nullable, ISO 8601 format) if it doesn't exist
        if "cancelled_at" not in column_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN cancelled_at TEXT")

        # Add cancel_reason column (nullable) if it doesn't exist
        if "cancel_reason" not in column_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN cancel_reason TEXT")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to migrate to version 2: {e}") from e


def _migrate_to_version_3(conn: sqlite3.Connection) -> None:
    """Migrate database from version 2 to version 3.

    Adds deferred_at and defer_reason columns to tasks table.

    Args:
        conn: Database connection.

    Raises:
        DatabaseError: If migration fails.
    """
    try:
        cursor = conn.cursor()

        # Check if columns already exist (for idempotency)
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Add deferred_at column (nullable, ISO 8601 format) if it doesn't exist
        if "deferred_at" not in column_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN deferred_at TEXT")

        # Add defer_reason column (nullable) if it doesn't exist
        if "defer_reason" not in column_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN defer_reason TEXT")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to migrate to version 3: {e}") from e
