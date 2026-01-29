"""Schema versioning and migration system.

This module handles database schema migrations for jot-cli. Migrations are
applied automatically when get_connection() is called.

ADDING A NEW MIGRATION:
=======================
1. Increment CURRENT_SCHEMA_VERSION in connection.py (e.g., 4 → 5)
2. Add a new function: _migrate_to_version_N(conn) in this file
3. Add the migration call in migrate_schema() below the existing ones:
       if current_version < N:
           _migrate_to_version_N(conn)
           current_version = N
4. Update schema.sql to reflect the final schema state (for fresh installs)
5. Tests use CURRENT_SCHEMA_VERSION constant - NO test updates needed!

MIGRATION GUIDELINES:
=====================
- Migrations must be idempotent (safe to run multiple times)
- Check if columns/tables exist before adding them
- Use transactions for data integrity
- Handle errors with conn.rollback() and raise DatabaseError
- SQLite doesn't support ALTER TABLE for CHECK constraints - recreate table
"""

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

            if current_version < 4:
                _migrate_to_version_4(conn)
                current_version = 4

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

    Adds deferred_at, defer_reason, and deferred_until columns to tasks table.

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

        # Add deferred_until column (nullable, ISO 8601 format) if it doesn't exist
        if "deferred_until" not in column_names:
            cursor.execute("ALTER TABLE tasks ADD COLUMN deferred_until TEXT")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to migrate to version 3: {e}") from e


def _migrate_to_version_4(conn: sqlite3.Connection) -> None:
    """Migrate database from version 3 to version 4.

    Adds 'RESUMED' to the event_type CHECK constraint in task_events table.

    Args:
        conn: Database connection.

    Raises:
        DatabaseError: If migration fails.
    """
    try:
        cursor = conn.cursor()

        # SQLite doesn't support ALTER TABLE to modify CHECK constraints,
        # so we need to recreate the table
        # Create new table with updated CHECK constraint
        cursor.execute("""
            CREATE TABLE task_events_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('CREATED', 'COMPLETED', 'CANCELLED', 'DEFERRED', 'RESUMED')),
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
            """)

        # Copy all data from old table to new table
        cursor.execute("""
            INSERT INTO task_events_new (id, task_id, event_type, timestamp, metadata)
            SELECT id, task_id, event_type, timestamp, metadata
            FROM task_events
            """)

        # Drop old table
        cursor.execute("DROP TABLE task_events")

        # Rename new table to original name
        cursor.execute("ALTER TABLE task_events_new RENAME TO task_events")

        # Recreate index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_events_task_id ON task_events(task_id)")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(f"Failed to migrate to version 4: {e}") from e
