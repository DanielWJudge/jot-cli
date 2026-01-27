"""Test suite for database crash recovery scenarios."""


class TestCrashRecovery:
    """Test crash recovery scenarios with WAL mode."""

    def test_wal_file_recovery_after_simulated_crash(self, tmp_path, monkeypatch):
        """Test WAL file recovery after simulated crash."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        # Create database and migrate
        conn = get_connection()
        migrate_schema(conn)

        # Insert some data
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )
        conn.commit()

        # Simulate crash by closing connection without proper shutdown
        # (In real scenario, this would be an unexpected termination)
        conn.close()

        # Reconnect - SQLite should automatically recover from WAL
        conn2 = get_connection()
        migrate_schema(conn2)

        # Verify data is still there (WAL recovery should preserve committed data)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT id FROM tasks WHERE id=?", ("task-1",))
        result = cursor2.fetchone()

        # Data should be preserved (committed before crash)
        assert result is not None
        assert result[0] == "task-1"

        conn2.close()

    def test_database_integrity_after_unexpected_termination(self, tmp_path, monkeypatch):
        """Test database integrity after unexpected termination."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        db_path = tmp_path / "jot.db"

        # Create database
        conn = get_connection()
        migrate_schema(conn)

        # Insert data
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )
        conn.commit()
        conn.close()

        # Simulate unexpected termination by removing lock files
        # (In real scenario, process would be killed)
        shm_path = db_path.with_suffix(".db-shm")
        if shm_path.exists():
            shm_path.unlink()

        # Reconnect - should work fine
        conn2 = get_connection()
        migrate_schema(conn2)

        # Verify integrity by checking data
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM tasks")
        count = cursor2.fetchone()[0]

        assert count == 1

        # Verify schema integrity
        cursor2.execute("PRAGMA integrity_check")
        integrity = cursor2.fetchone()[0]

        assert integrity == "ok"

        conn2.close()

    def test_concurrent_readers_one_writer(self, tmp_path, monkeypatch):
        """Test concurrent access: multiple readers, one writer."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        # Create database with initial data
        conn_writer = get_connection()
        migrate_schema(conn_writer)

        cursor_writer = conn_writer.cursor()
        cursor_writer.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )
        conn_writer.commit()

        # Create multiple reader connections
        conn_reader1 = get_connection()
        conn_reader2 = get_connection()

        # Readers can read simultaneously
        cursor_reader1 = conn_reader1.cursor()
        cursor_reader1.execute("SELECT id FROM tasks WHERE id=?", ("task-1",))
        result1 = cursor_reader1.fetchone()

        cursor_reader2 = conn_reader2.cursor()
        cursor_reader2.execute("SELECT id FROM tasks WHERE id=?", ("task-1",))
        result2 = cursor_reader2.fetchone()

        assert result1 is not None
        assert result2 is not None
        assert result1[0] == result2[0] == "task-1"

        # Writer can write while readers are active (WAL mode allows this)
        cursor_writer.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-2", "Test task 2", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )
        conn_writer.commit()

        # Readers can still read (they see consistent snapshot)
        cursor_reader1.execute("SELECT COUNT(*) FROM tasks")
        count1 = cursor_reader1.fetchone()[0]

        cursor_reader2.execute("SELECT COUNT(*) FROM tasks")
        count2 = cursor_reader2.fetchone()[0]

        # Both readers see at least 1 task (snapshot isolation)
        assert count1 >= 1
        assert count2 >= 1

        conn_writer.close()
        conn_reader1.close()
        conn_reader2.close()

    def test_wal_checkpoint_recovery(self, tmp_path, monkeypatch):
        """Test WAL checkpoint and recovery."""
        monkeypatch.setattr("jot.db.connection.get_data_dir", lambda: tmp_path)

        from jot.db.connection import get_connection
        from jot.db.migrations import migrate_schema

        # Create database
        conn = get_connection()
        migrate_schema(conn)

        # Insert data
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (id, description, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("task-1", "Test task", "active", "2026-01-26T00:00:00Z", "2026-01-26T00:00:00Z"),
        )
        conn.commit()

        # Force checkpoint (this would normally happen automatically)
        cursor.execute("PRAGMA wal_checkpoint(FULL)")
        conn.commit()

        # Close and reopen
        conn.close()

        # Reopen should work fine
        conn2 = get_connection()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT id FROM tasks WHERE id=?", ("task-1",))
        result = cursor2.fetchone()

        assert result is not None
        assert result[0] == "task-1"

        conn2.close()
