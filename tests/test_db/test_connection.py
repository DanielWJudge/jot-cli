"""Test suite for db.connection module."""

import os

import pytest

from jot.db.exceptions import DatabaseError


class TestDatabaseConnection:
    """Test database connection creation and configuration."""

    def test_creates_database_at_correct_location(self, tmp_path, monkeypatch):
        """Test database is created at XDG data directory."""
        # Mock get_data_dir to use temp directory
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection

        db_path = tmp_path / "jot.db"
        conn = get_connection()

        assert db_path.exists()
        assert conn is not None
        conn.close()

    def test_enables_wal_mode(self, tmp_path, monkeypatch):
        """Test WAL mode is enabled."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode.lower() == "wal"
        conn.close()

    def test_sets_database_permissions(self, tmp_path, monkeypatch):
        """Test database file has restrictive permissions (0600)."""
        if os.name == "nt":  # Skip on Windows
            pytest.skip("File permissions not applicable on Windows")

        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection

        conn = get_connection()
        conn.close()

        db_path = tmp_path / "jot.db"
        stat_info = os.stat(db_path)
        permissions = stat_info.st_mode & 0o777

        assert permissions == 0o600

    def test_sets_schema_version(self, tmp_path, monkeypatch):
        """Test PRAGMA user_version is set."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]

        assert version == 2  # Should be set to current schema version
        conn.close()

    def test_creates_initial_schema(self, tmp_path, monkeypatch):
        """Test tasks and task_events tables are created."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('tasks', 'task_events')"
        )
        table_names = {row[0] for row in cursor.fetchall()}

        assert table_names == {"tasks", "task_events"}
        conn.close()

    def test_handles_directory_creation(self, tmp_path, monkeypatch):
        """Test database directory creation if needed."""
        # Create a subdirectory that doesn't exist yet
        db_dir = tmp_path / "new_dir"
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: db_dir)

        from jot.db.connection import get_connection

        conn = get_connection()
        db_path = db_dir / "jot.db"

        assert db_dir.exists()
        assert db_path.exists()
        conn.close()

    def test_raises_database_error_on_failure(self, tmp_path, monkeypatch):
        """Test DatabaseError is raised on connection failure."""

        # Mock get_data_dir to raise OSError
        def raise_error():
            raise OSError("Cannot create directory")

        monkeypatch.setattr("jot.db.connection.get_data_dir", raise_error)

        from jot.db.connection import get_connection

        with pytest.raises(DatabaseError) as exc_info:
            get_connection()

        assert "Cannot create database" in str(exc_info.value.message)
