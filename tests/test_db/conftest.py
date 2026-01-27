"""Shared pytest fixtures for database tests."""

from pathlib import Path

import pytest


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a temporary database path for testing."""
    return tmp_path / "jot.db"


@pytest.fixture
def mock_data_dir(monkeypatch, tmp_path: Path):
    """Mock get_data_dir to return temporary directory."""
    monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("jot.db.migrations.get_data_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def clean_db(mock_data_dir, db_path: Path):
    """Provide a clean database connection with schema migrated."""
    from jot.db.connection import get_connection
    from jot.db.migrations import migrate_schema

    # Remove existing database if present
    if db_path.exists():
        db_path.unlink()

    conn = get_connection()
    migrate_schema(conn)
    yield conn
    conn.close()

    # Cleanup: remove database file
    if db_path.exists():
        db_path.unlink()
        # Also remove WAL and SHM files if they exist
        wal_path = db_path.with_suffix(".db-wal")
        shm_path = db_path.with_suffix(".db-shm")
        if wal_path.exists():
            wal_path.unlink()
        if shm_path.exists():
            shm_path.unlink()


@pytest.fixture
def corrupted_db(mock_data_dir, db_path: Path):
    """Create a corrupted database file for testing recovery."""
    # Create a database file with invalid SQLite header
    db_path.write_bytes(b"INVALID_SQLITE_HEADER" + b"\x00" * 100)
    return db_path
