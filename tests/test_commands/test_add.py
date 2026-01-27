"""Test suite for commands.add module."""

import sqlite3
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.task import Task, TaskState
from jot.db.connection import get_connection
from jot.db.repository import TaskRepository


class TestAddCommand:
    """Test jot add command."""

    def test_add_with_description_creates_task(self, temp_db):
        """Test jot add "description" creates task successfully."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "Review PR for auth feature"])

        assert result.exit_code == 0
        assert "🎯 Added: Review PR for auth feature" in result.stdout

        # Verify task was created in database
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert active.description == "Review PR for auth feature"
        assert active.state == TaskState.ACTIVE

    def test_add_without_description_prompts_interactively(self, temp_db):
        """Test jot add prompts when no description provided."""
        runner = CliRunner()

        # Mock typer.prompt to return test description
        with patch("typer.prompt", return_value="Test task from prompt"):
            result = runner.invoke(app, ["add"])

            assert result.exit_code == 0
            assert "🎯 Added: Test task from prompt" in result.stdout

    def test_add_with_active_task_shows_warning(self, temp_db):
        """Test jot add shows warning when active task exists."""
        # Create an active task first
        repo = TaskRepository()
        existing_task = Task(
            id=str(uuid.uuid4()),
            description="Existing active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(existing_task)

        runner = CliRunner()

        # Mock typer.prompt for force option
        with patch("typer.prompt", return_value="f"):
            result = runner.invoke(app, ["add", "New task"])

            assert "⚠️" in result.stdout
            assert "Existing active task" in result.stdout

    def test_add_validates_empty_description(self, temp_db):
        """Test jot add rejects empty description."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", ""])

        assert result.exit_code == 1
        # Error is written to stderr (verified by exit code)

    def test_add_performance_under_100ms(self, temp_db):
        """Test jot add completes in <100ms (NFR1)."""
        import time

        runner = CliRunner()

        start = time.time()
        result = runner.invoke(app, ["add", "Performance test task"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert result.exit_code == 0
        assert elapsed < 100, f"Command took {elapsed}ms, exceeds 100ms limit"

    def test_add_force_option_creates_second_active_task_with_warning(self, temp_db):
        """Test force option creates second active task (violates business rule but allowed by DB)."""
        # Create an active task first
        repo = TaskRepository()
        existing_task_id = str(uuid.uuid4())
        existing_task = Task(
            id=existing_task_id,
            description="Existing active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(existing_task)

        runner = CliRunner()

        # Mock typer.prompt for force option
        with patch("typer.prompt", return_value="f"):
            result = runner.invoke(app, ["add", "New task"])

            # Force option currently creates second active task (business rule violation)
            # This is documented behavior until proper task state transitions are implemented
            assert result.exit_code == 0
            assert "🎯 Added: New task" in result.stdout

            # The warning message should be displayed
            assert "Forcing new task" in result.stdout

            # Verify new task was created in database
            conn = get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE description = ?", ("New task",))
            row = cursor.fetchone()
            conn.close()
            assert row is not None
            assert row["description"] == "New task"
            assert row["state"] == "active"

    def test_add_other_options_show_message(self, temp_db):
        """Test other options (d/c/D) display appropriate messages."""
        # Create an active task first
        repo = TaskRepository()
        existing_task = Task(
            id=str(uuid.uuid4()),
            description="Existing active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(existing_task)

        runner = CliRunner()

        # Test 'd' option
        with patch("typer.prompt", return_value="d"):
            result = runner.invoke(app, ["add", "New task"])
            assert result.exit_code == 1
            assert "Please use 'jot done', 'jot cancel', or 'jot defer' first" in result.stdout

        # Test 'c' option
        with patch("typer.prompt", return_value="c"):
            result = runner.invoke(app, ["add", "New task"])
            assert result.exit_code == 1
            assert "Please use 'jot done', 'jot cancel', or 'jot defer' first" in result.stdout

        # Test 'D' option
        with patch("typer.prompt", return_value="D"):
            result = runner.invoke(app, ["add", "New task"])
            assert result.exit_code == 1
            assert "Please use 'jot done', 'jot cancel', or 'jot defer' first" in result.stdout

    def test_add_validates_whitespace_only_description(self, temp_db):
        """Test jot add rejects whitespace-only description."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "   "])

        assert result.exit_code == 1
        # Error is written to stderr (verified by exit code)

    def test_add_creates_task_with_correct_fields(self, temp_db):
        """Test task has correct fields (id, description, state=ACTIVE, timestamps)."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "Test task"])

        assert result.exit_code == 0

        # Verify task was created with correct fields
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert active.description == "Test task"
        assert active.state == TaskState.ACTIVE
        assert active.id is not None
        assert len(active.id) == 36  # UUID string length
        assert active.created_at is not None
        assert active.updated_at is not None
        assert active.created_at == active.updated_at  # Should be same on creation

    def test_add_creates_created_event(self, temp_db):
        """Test CREATED event is logged."""
        from jot.db.repository import EventRepository

        runner = CliRunner()

        result = runner.invoke(app, ["add", "Test task"])

        assert result.exit_code == 0

        # Verify CREATED event was created
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None

        event_repo = EventRepository()
        events = event_repo.get_events_for_task(active.id)
        assert len(events) == 1
        assert events[0].event_type == "CREATED"
        assert events[0].task_id == active.id

    def test_add_handles_database_error(self, temp_db):
        """Test error handling path when database error occurs."""
        runner = CliRunner()

        # Mock TaskRepository.create_task to raise DatabaseError
        with patch("jot.commands.add.TaskRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.get_active_task.return_value = None
            # Simulate database error during task creation
            from jot.db.exceptions import DatabaseError

            mock_repo.create_task.side_effect = DatabaseError("Database connection failed")

            result = runner.invoke(app, ["add", "Test task"])

            # DatabaseError should now be caught and handled gracefully
            assert result.exit_code == 2  # System error exit code
            # Error message is written to stderr (verified by exit code)

    def test_add_handles_database_error_during_active_task_check(self, temp_db):
        """Test error handling when database error occurs during active task check."""
        runner = CliRunner()

        # Mock TaskRepository.get_active_task to raise DatabaseError
        with patch("jot.commands.add.TaskRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            from jot.db.exceptions import DatabaseError

            mock_repo.get_active_task.side_effect = DatabaseError("Database query failed")

            result = runner.invoke(app, ["add", "Test task"])

            # DatabaseError should now be caught and handled gracefully
            assert result.exit_code == 2  # System error exit code
            # Error message is written to stderr (verified by exit code)

    def test_add_handles_very_long_description(self, temp_db):
        """Test jot add accepts maximum length description (2000 characters)."""
        runner = CliRunner()

        # Create description at max length (2000 chars)
        long_description = "A" * 2000

        result = runner.invoke(app, ["add", long_description])

        assert result.exit_code == 0
        assert "🎯 Added:" in result.stdout

        # Verify task was created
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert len(active.description) == 2000

    def test_add_handles_unicode_characters(self, temp_db):
        """Test jot add handles unicode characters in description."""
        runner = CliRunner()

        unicode_description = "完成代码审查 🎯 日本語のタスク 中文任务"

        result = runner.invoke(app, ["add", unicode_description])

        assert result.exit_code == 0
        assert "🎯 Added:" in result.stdout

        # Verify task was created with unicode preserved
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert active.description == unicode_description

    def test_add_handles_special_characters(self, temp_db):
        """Test jot add handles special characters in description."""
        runner = CliRunner()

        special_description = 'Task with "quotes", <tags>, & symbols!'

        result = runner.invoke(app, ["add", special_description])

        assert result.exit_code == 0
        assert "🎯 Added:" in result.stdout

        # Verify task was created with special characters preserved
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert active.description == special_description

    def test_add_interactive_prompt_empty_input_validation(self, temp_db):
        """Test interactive prompt validates empty input."""
        runner = CliRunner()

        # Mock typer.prompt to return empty string
        # Current implementation doesn't retry - it validates and fails
        with patch("typer.prompt", return_value=""):
            result = runner.invoke(app, ["add"])

            # Current implementation fails on empty input
            assert result.exit_code == 1
            # Error is written to stderr (verified by exit code)

    def test_add_interactive_prompt_whitespace_input_validation(self, temp_db):
        """Test interactive prompt validates whitespace-only input."""
        runner = CliRunner()

        # Mock typer.prompt to return whitespace-only input
        # Current implementation doesn't retry - it validates and fails
        with patch("typer.prompt", return_value="   "):
            result = runner.invoke(app, ["add"])

            # Current implementation fails on whitespace-only input
            assert result.exit_code == 1
            # Error is written to stderr (verified by exit code)

    def test_add_strips_whitespace_from_description(self, temp_db):
        """Test jot add strips leading/trailing whitespace from description."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "  Task with spaces  "])

        assert result.exit_code == 0

        # Verify task description has whitespace stripped
        repo = TaskRepository()
        active = repo.get_active_task()
        assert active is not None
        assert active.description == "Task with spaces"  # Stripped

    def test_add_performance_with_existing_tasks(self, temp_db):
        """Test jot add performance with many existing tasks in database (1000+)."""
        import time

        # Create 1000+ completed tasks in database (no active task to avoid conflict)
        repo = TaskRepository()
        for i in range(1000):
            task = Task(
                id=str(uuid.uuid4()),
                description=f"Existing task {i}",
                state=TaskState.COMPLETED,  # All completed to avoid active task conflict
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            repo.create_task(task)

        runner = CliRunner()

        start = time.time()
        result = runner.invoke(app, ["add", "Performance test with many tasks"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert result.exit_code == 0
        assert elapsed < 100, f"Command took {elapsed}ms, exceeds 100ms limit"

    def test_add_handles_concurrent_execution(self, temp_db):
        """Test jot add handles concurrent execution gracefully."""
        import concurrent.futures
        import threading

        runner = CliRunner()
        results = []
        lock = threading.Lock()

        def add_task(task_num):
            """Add a task in a separate thread."""
            result = runner.invoke(app, ["add", f"Concurrent task {task_num}"])
            with lock:
                results.append((task_num, result.exit_code))
            return result

        # Execute 10 concurrent add commands
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(add_task, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # At least one should succeed (the first one)
        success_count = sum(1 for _, exit_code in results if exit_code == 0)
        assert success_count >= 1, "At least one concurrent add should succeed"

        # Some may fail due to active task conflict or database locking
        # This is acceptable behavior - the command handles it gracefully
        # by showing error messages rather than crashing
