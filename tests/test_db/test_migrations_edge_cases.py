"""Test suite for db.migrations edge cases and error scenarios."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jot.db.exceptions import DatabaseError


class TestMigrationsEdgeCases:
    """Test edge cases and error scenarios for migration system."""

    def test_get_schema_version_with_closed_connection_raises_error(self, tmp_path, monkeypatch):
        """Test that get_schema_version raises error with closed connection."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version

        conn = get_connection()
        conn.close()

        # Try to get schema version with closed connection
        with pytest.raises(DatabaseError):
            get_schema_version(conn)

    def test_migration_with_closed_connection_raises_error(self, tmp_path, monkeypatch):
        """Test that migration with closed connection raises DatabaseError."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        conn.close()

        # Try to migrate with closed connection
        with pytest.raises(DatabaseError):
            migrate_schema(conn)

    def test_migration_error_handling_with_sqlite_error(self, tmp_path, monkeypatch):
        """Test that migration error handling works correctly."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()

        # Close connection to simulate error scenario
        conn.close()

        # Try to migrate with closed connection - should raise DatabaseError
        with pytest.raises(DatabaseError):
            migrate_schema(conn)

    def test_migration_with_missing_schema_file(self, tmp_path, monkeypatch):
        """Test that migration handles missing schema.sql file."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import _migrate_to_version_1

        conn = get_connection()

        # Mock Path to simulate missing file
        with patch("jot.db.migrations.Path") as mock_path:
            mock_schema_path = MagicMock()
            mock_schema_path.__truediv__.return_value = mock_schema_path
            mock_schema_path.parent = MagicMock()
            mock_schema_path.parent.__truediv__.return_value = Path("/nonexistent/schema.sql")
            mock_path.return_value = mock_schema_path

            # This should raise FileNotFoundError, which will be caught and converted
            with pytest.raises((FileNotFoundError, DatabaseError)):
                _migrate_to_version_1(conn)

        conn.close()

    def test_migration_idempotency_multiple_calls(self, tmp_path, monkeypatch):
        """Test that calling migrate_schema multiple times is safe."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        conn = get_connection()

        # First migration
        migrate_schema(conn)
        version1 = get_schema_version(conn)
        assert version1 == 3  # Updated to version 3

        # Second migration (should be idempotent)
        migrate_schema(conn)
        version2 = get_schema_version(conn)
        assert version2 == 3  # Updated to version 3

        # Third migration (should still be idempotent)
        migrate_schema(conn)
        version3 = get_schema_version(conn)
        assert version3 == 3  # Updated to version 3

        # Verify tables still exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        result = cursor.fetchone()
        assert result is not None

        conn.close()

    def test_schema_version_edge_cases(self, tmp_path, monkeypatch):
        """Test schema version edge cases."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version

        conn = get_connection()

        # get_connection auto-migrates to current schema
        version = get_schema_version(conn)
        assert version == 3  # Updated to version 3

        # Manually set version to a high number
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version = 999")
        conn.commit()

        version = get_schema_version(conn)
        assert version == 999

        conn.close()

    def test_migration_from_version_1_to_version_3(self, tmp_path, monkeypatch):
        """Test migration from schema version 1 to version 3 (via version 2)."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        import sqlite3

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        # Create a version 1 database manually
        db_path = tmp_path / "jot.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create version 1 schema (without cancelled_at, cancel_reason, deferred_at, defer_reason)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('active', 'completed', 'cancelled', 'deferred')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                deferred_until TEXT
            )
            """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL CHECK(event_type IN ('CREATED', 'COMPLETED', 'CANCELLED', 'DEFERRED')),
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
            """)

        # Set version to 1
        cursor.execute("PRAGMA user_version = 1")
        conn.commit()

        # Insert a test task
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("test-id", "Test task", "active", "2026-01-27T10:00:00Z", "2026-01-27T10:00:00Z"),
        )
        conn.commit()
        conn.close()

        # Now migrate to version 3 (via version 2)
        conn = get_connection()
        migrate_schema(conn)

        # Verify version is now 3
        version = get_schema_version(conn)
        assert version == 3

        # Verify cancelled_at, cancel_reason, deferred_at, and defer_reason columns exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        assert "cancelled_at" in column_names
        assert "cancel_reason" in column_names
        assert "deferred_at" in column_names
        assert "defer_reason" in column_names

        # Verify existing task has NULL values for new columns
        cursor.execute(
            "SELECT cancelled_at, cancel_reason, deferred_at, defer_reason FROM tasks WHERE id = ?",
            ("test-id",),
        )
        row = cursor.fetchone()
        assert row[0] is None  # cancelled_at
        assert row[1] is None  # cancel_reason
        assert row[2] is None  # deferred_at
        assert row[3] is None  # defer_reason

        conn.close()

    def test_migration_to_version_3_idempotent(self, tmp_path, monkeypatch):
        """Test that migration to version 3 is idempotent."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        conn = get_connection()

        # First migration (should migrate to version 3)
        migrate_schema(conn)
        version1 = get_schema_version(conn)
        assert version1 == 3

        # Second migration (should be idempotent)
        migrate_schema(conn)
        version2 = get_schema_version(conn)
        assert version2 == 3

        # Third migration (should still be idempotent)
        migrate_schema(conn)
        version3 = get_schema_version(conn)
        assert version3 == 3

        # Verify columns still exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        assert "cancelled_at" in column_names
        assert "cancel_reason" in column_names
        assert "deferred_at" in column_names
        assert "defer_reason" in column_names

        conn.close()
