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
        assert version1 == 1

        # Second migration (should be idempotent)
        migrate_schema(conn)
        version2 = get_schema_version(conn)
        assert version2 == 1

        # Third migration (should still be idempotent)
        migrate_schema(conn)
        version3 = get_schema_version(conn)
        assert version3 == 1

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
        assert version == 1

        # Manually set version to a high number
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version = 999")
        conn.commit()

        version = get_schema_version(conn)
        assert version == 999

        conn.close()
