"""Database connection management with WAL mode and permissions."""

import os
import sqlite3

from jot.config.paths import get_data_dir
from jot.db.exceptions import DatabaseError

# Schema version constant - the single source of truth for database schema version.
#
# IMPORTANT: When adding a new migration:
# 1. Increment this constant (e.g., 4 → 5)
# 2. Add a new _migrate_to_version_N function in migrations.py
# 3. Update migrate_schema() to call the new migration function
# 4. Update schema.sql to reflect the final schema state
# 5. Tests automatically use this constant - no test updates needed!
#
# See migrations.py for migration implementation details.
CURRENT_SCHEMA_VERSION = 4


def get_connection() -> sqlite3.Connection:
    """Get SQLite database connection with WAL mode enabled.

    Creates database file at XDG data directory if it doesn't exist.
    Enables WAL mode for crash resistance and better concurrency.
    Sets database file permissions to 0600 (owner read/write only).

    Returns:
        sqlite3.Connection: Database connection with WAL mode enabled.

    Raises:
        DatabaseError: If database cannot be created or accessed.
    """
    try:
        data_dir = get_data_dir()
        db_path = data_dir / "jot.db"

        # Ensure directory exists (get_data_dir creates it, but handle edge cases)
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create connection (creates file if doesn't exist)
        conn = sqlite3.connect(str(db_path))

        # Enable WAL mode
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        result = cursor.fetchone()
        if result[0].lower() != "wal":
            raise DatabaseError("Failed to enable WAL mode")

        # Set synchronous mode for WAL (NORMAL balances performance/durability)
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Set database file permissions (Unix only)
        if os.name != "nt":  # Not Windows
            os.chmod(db_path, 0o600)

        # Ensure schema is migrated/initialized before use
        from jot.db.migrations import migrate_schema

        migrate_schema(conn)

        return conn

    except OSError as e:
        raise DatabaseError(f"Cannot create database: {e}") from e
    except sqlite3.Error as e:
        raise DatabaseError(f"Database error: {e}") from e
