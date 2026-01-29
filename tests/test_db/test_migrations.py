"""Test suite for db.migrations module."""

import pytest

from jot.db.exceptions import DatabaseError


class TestMigrationSystem:
    """Test schema versioning and migration system."""

    def test_initial_schema_creation(self, tmp_path, monkeypatch):
        """Test initial schema creation (version 0 → 3)."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        conn = get_connection()

        # get_connection auto-migrates to current schema
        version = get_schema_version(conn)
        assert version == 3

        # Migrate to version 3
        migrate_schema(conn)

        # Should now be version 3
        version = get_schema_version(conn)
        assert version == 3

        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        result = cursor.fetchone()
        assert result is not None

        conn.close()

    def test_schema_version_tracking(self, tmp_path, monkeypatch):
        """Test schema version tracking (PRAGMA user_version)."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        conn = get_connection()

        # get_connection auto-migrates to current schema
        version = get_schema_version(conn)
        assert version == 3

        # Migrate
        migrate_schema(conn)

        # Check version after migration
        version = get_schema_version(conn)
        assert version == 3

        # Verify PRAGMA user_version directly
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version")
        pragma_version = cursor.fetchone()[0]
        assert pragma_version == 3

        conn.close()

    def test_migration_idempotency(self, tmp_path, monkeypatch):
        """Test migration idempotency (running migration twice is safe)."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import get_schema_version, migrate_schema

        conn = get_connection()

        # First migration
        migrate_schema(conn)
        version1 = get_schema_version(conn)
        assert version1 == 3

        # Second migration (should be safe)
        migrate_schema(conn)
        version2 = get_schema_version(conn)
        assert version2 == 3

        # Verify tables still exist and are correct
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        result = cursor.fetchone()
        assert result is not None

        conn.close()

    def test_get_schema_version_creates_connection_if_none(self, tmp_path, monkeypatch):
        """Test get_schema_version creates connection if None provided."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.migrations import get_schema_version, migrate_schema

        # Call without connection
        version = get_schema_version()
        assert version == 3

        # Migrate
        migrate_schema()

        # Check version again
        version = get_schema_version()
        assert version == 3

    def test_migrate_schema_creates_connection_if_none(self, tmp_path, monkeypatch):
        """Test migrate_schema creates connection if None provided."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.migrations import get_schema_version, migrate_schema

        # Migrate without connection
        migrate_schema()

        # Verify migration worked
        version = get_schema_version()
        assert version == 3

    def test_migration_error_handling(self, tmp_path, monkeypatch):
        """Test migration error handling."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()

        # Close connection to cause error
        conn.close()

        # Try to migrate with closed connection
        with pytest.raises(DatabaseError):
            migrate_schema(conn)
