"""Test suite for db.schema module."""

import sqlite3

import pytest


class TestDatabaseSchema:
    """Test database schema structure and constraints."""

    def test_tasks_table_exists_with_correct_columns(self, tmp_path, monkeypatch):
        """Test tasks table exists with correct columns."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        result = cursor.fetchone()

        assert result is not None

        # Check columns
        cursor.execute("PRAGMA table_info(tasks)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert columns["id"] == "TEXT"
        assert "description" in columns
        assert columns["description"] == "TEXT"
        assert "state" in columns
        assert columns["state"] == "TEXT"
        assert "created_at" in columns
        assert columns["created_at"] == "TEXT"
        assert "updated_at" in columns
        assert columns["updated_at"] == "TEXT"
        assert "completed_at" in columns
        assert "deferred_until" in columns

        conn.close()

    def test_task_events_table_exists_with_correct_columns(self, tmp_path, monkeypatch):
        """Test task_events table exists with correct columns."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_events'")
        result = cursor.fetchone()

        assert result is not None

        # Check columns
        cursor.execute("PRAGMA table_info(task_events)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert columns["id"] == "INTEGER"
        assert "task_id" in columns
        assert columns["task_id"] == "TEXT"
        assert "event_type" in columns
        assert columns["event_type"] == "TEXT"
        assert "timestamp" in columns
        assert columns["timestamp"] == "TEXT"
        assert "metadata" in columns

        conn.close()

    def test_check_constraint_on_tasks_state(self, tmp_path, monkeypatch):
        """Test CHECK constraint on tasks.state (rejects invalid states)."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()

        # Valid states should work
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("test-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )

        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("test-2", "Test task", "completed", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )

        # Invalid state should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO tasks (id, description, state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("test-3", "Test task", "invalid", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
            )

        conn.close()

    def test_foreign_key_constraint_on_task_events_task_id(self, tmp_path, monkeypatch):
        """Test foreign key constraint on task_events.task_id."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        # Enable foreign key constraints
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")

        # Create a task first
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("test-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )

        # Valid foreign key should work
        cursor.execute(
            """
            INSERT INTO task_events (task_id, event_type, timestamp)
            VALUES (?, ?, ?)
            """,
            ("test-1", "CREATED", "2026-01-26T00:00:00Z"),
        )

        # Invalid foreign key should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO task_events (task_id, event_type, timestamp)
                VALUES (?, ?, ?)
                """,
                ("nonexistent", "CREATED", "2026-01-26T00:00:00Z"),
            )

        conn.close()

    def test_indexes_exist(self, tmp_path, monkeypatch):
        """Test indexes exist on tasks.state and task_events.task_id."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tasks_state'"
        )
        result = cursor.fetchone()

        assert result is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_task_events_task_id'"
        )
        result = cursor.fetchone()

        assert result is not None

        conn.close()

    def test_timestamp_columns_accept_iso8601_format(self, tmp_path, monkeypatch):
        """Test timestamp columns accept ISO8601 format."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()

        # ISO8601 format should work
        iso8601_timestamp = "2026-01-26T12:34:56Z"
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "test-1",
                "Test task",
                "completed",
                iso8601_timestamp,
                iso8601_timestamp,
                iso8601_timestamp,
            ),
        )

        cursor.execute(
            "SELECT created_at, updated_at, completed_at FROM tasks WHERE id=?", ("test-1",)
        )
        row = cursor.fetchone()

        assert row[0] == iso8601_timestamp
        assert row[1] == iso8601_timestamp
        assert row[2] == iso8601_timestamp

        conn.close()

    def test_nullable_columns_allow_null_values(self, tmp_path, monkeypatch):
        """Test nullable columns allow NULL values."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        conn = get_connection()
        migrate_schema(conn)

        cursor = conn.cursor()

        # Nullable columns should allow NULL
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("test-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )

        cursor.execute(
            "SELECT completed_at, deferred_until FROM tasks WHERE id=?",
            ("test-1",),
        )
        row = cursor.fetchone()

        assert row[0] is None  # completed_at
        assert row[1] is None  # deferred_until

        conn.close()
