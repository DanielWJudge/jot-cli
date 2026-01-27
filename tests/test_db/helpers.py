"""Helper utilities for database tests."""

import sqlite3
from pathlib import Path


def create_test_database(db_path: Path, schema_version: int = 0) -> sqlite3.Connection:
    """Create a test database with specified schema version.

    Args:
        db_path: Path to database file.
        schema_version: Schema version to set (default: 0).

    Returns:
        sqlite3.Connection: Database connection.
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA user_version = {schema_version}")
    conn.commit()
    return conn


def corrupt_database(db_path: Path) -> None:
    """Corrupt a database file by writing invalid data.

    Args:
        db_path: Path to database file.
    """
    # Write invalid SQLite header
    db_path.write_bytes(b"INVALID_SQLITE_HEADER" + b"\x00" * 100)


def create_wal_file(db_path: Path) -> Path:
    """Create a WAL file for testing WAL recovery scenarios.

    Args:
        db_path: Path to database file.

    Returns:
        Path: Path to created WAL file.
    """
    wal_path = db_path.with_suffix(".db-wal")
    # Write minimal WAL header (SQLite WAL format)
    wal_path.write_bytes(
        b"\x37\x7f\x06\x82"  # WAL magic number
        + b"\x00\x00\x00\x00"  # File format version
        + b"\x00\x00\x00\x00"  # Page size
        + b"\x00\x00\x00\x00"  # Checkpoint sequence number
        + b"\x00\x00\x00\x00"  # Salt 1
        + b"\x00\x00\x00\x00"  # Salt 2
        + b"\x00\x00\x00\x00"  # Checksum 1
        + b"\x00\x00\x00\x00"  # Checksum 2
        + b"\x00" * 24  # Padding
    )
    return wal_path


def get_wal_mode(conn: sqlite3.Connection) -> str:
    """Get current journal mode of database connection.

    Args:
        conn: Database connection.

    Returns:
        str: Journal mode (e.g., 'wal', 'delete', 'truncate').
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    result = cursor.fetchone()
    return result[0].lower() if result else "unknown"


def get_schema_version_from_db(conn: sqlite3.Connection) -> int:
    """Get schema version from database connection.

    Args:
        conn: Database connection.

    Returns:
        int: Schema version.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    result = cursor.fetchone()
    return result[0] if result else 0
