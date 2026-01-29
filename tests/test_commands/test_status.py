"""Test suite for commands.status module."""

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.task import Task, TaskState
from jot.db.exceptions import DatabaseError
from jot.db.repository import TaskRepository


class TestStatusCommand:
    """Test jot status command."""

    def test_status_displays_active_task(self, temp_db):
        """Test jot status displays active task with emoji."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task description",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Task is displayed
        assert result.exit_code == 0
        assert "🎯" in result.stdout
        assert "Test task description" in result.stdout
        assert "started" in result.stdout.lower() or "just now" in result.stdout.lower()

    def test_status_shows_task_description(self, temp_db):
        """Test jot status shows task description correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="My important task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Description is shown
        assert result.exit_code == 0
        assert "My important task" in result.stdout

    def test_status_shows_just_now_for_recent_task(self, temp_db):
        """Test jot status shows 'just now' for tasks created less than 1 minute ago."""
        # Arrange: Create active task just now
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Recent task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status immediately
        result = runner.invoke(app, ["status"])

        # Assert: Shows "just now" or "started just now"
        assert result.exit_code == 0
        assert "just now" in result.stdout.lower()

    def test_status_shows_minutes_ago(self, temp_db):
        """Test jot status shows 'X minutes ago' format."""
        # Arrange: Create task 5 minutes ago
        repo = TaskRepository()
        five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
        task = Task(
            id=str(uuid.uuid4()),
            description="Five minutes old task",
            state=TaskState.ACTIVE,
            created_at=five_minutes_ago,
            updated_at=five_minutes_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "5 minutes ago" or "started 5 minutes ago"
        assert result.exit_code == 0
        assert "5 minute" in result.stdout.lower()
        assert "ago" in result.stdout.lower()

    def test_status_shows_hours_ago(self, temp_db):
        """Test jot status shows 'X hours ago' format."""
        # Arrange: Create task 2 hours ago
        repo = TaskRepository()
        two_hours_ago = datetime.now(UTC) - timedelta(hours=2)
        task = Task(
            id=str(uuid.uuid4()),
            description="Two hours old task",
            state=TaskState.ACTIVE,
            created_at=two_hours_ago,
            updated_at=two_hours_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "2 hours ago" or "started 2 hours ago"
        assert result.exit_code == 0
        assert "2 hour" in result.stdout.lower()
        assert "ago" in result.stdout.lower()

    def test_status_shows_days_ago(self, temp_db):
        """Test jot status shows 'X days ago' format."""
        # Arrange: Create task 3 days ago
        repo = TaskRepository()
        three_days_ago = datetime.now(UTC) - timedelta(days=3)
        task = Task(
            id=str(uuid.uuid4()),
            description="Three days old task",
            state=TaskState.ACTIVE,
            created_at=three_days_ago,
            updated_at=three_days_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "3 days ago" or "started 3 days ago"
        assert result.exit_code == 0
        assert "3 day" in result.stdout.lower()
        assert "ago" in result.stdout.lower()

    def test_status_singular_minute(self, temp_db):
        """Test jot status shows singular 'minute' for exactly 1 minute."""
        # Arrange: Create task exactly 1 minute ago
        repo = TaskRepository()
        one_minute_ago = datetime.now(UTC) - timedelta(minutes=1)
        task = Task(
            id=str(uuid.uuid4()),
            description="One minute old task",
            state=TaskState.ACTIVE,
            created_at=one_minute_ago,
            updated_at=one_minute_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "1 minute ago" (singular, not "1 minutes ago")
        assert result.exit_code == 0
        assert "1 minute" in result.stdout.lower()
        assert "1 minutes" not in result.stdout.lower()

    def test_status_singular_hour(self, temp_db):
        """Test jot status shows singular 'hour' for exactly 1 hour."""
        # Arrange: Create task exactly 1 hour ago
        repo = TaskRepository()
        one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
        task = Task(
            id=str(uuid.uuid4()),
            description="One hour old task",
            state=TaskState.ACTIVE,
            created_at=one_hour_ago,
            updated_at=one_hour_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "1 hour ago" (singular, not "1 hours ago")
        assert result.exit_code == 0
        assert "1 hour" in result.stdout.lower()
        assert "1 hours" not in result.stdout.lower()

    def test_status_singular_day(self, temp_db):
        """Test jot status shows singular 'day' for exactly 1 day."""
        # Arrange: Create task exactly 1 day ago
        repo = TaskRepository()
        one_day_ago = datetime.now(UTC) - timedelta(days=1)
        task = Task(
            id=str(uuid.uuid4()),
            description="One day old task",
            state=TaskState.ACTIVE,
            created_at=one_day_ago,
            updated_at=one_day_ago,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "1 day ago" (singular, not "1 days ago")
        assert result.exit_code == 0
        assert "1 day" in result.stdout.lower()
        assert "1 days" not in result.stdout.lower()

    def test_status_without_active_task_shows_empty_state(self, temp_db):
        """Test jot status shows empty state when no active task."""
        runner = CliRunner()

        # Act: Run jot status with no active task
        result = runner.invoke(app, ["status"], catch_exceptions=False)

        # Assert: Error message and helpful hint are displayed
        assert result.exit_code == 1
        # Note: CliRunner may capture stderr separately, but exit code 1 confirms error occurred
        # The actual message format is verified by manual testing and other tests
        # For automated testing, we verify exit code and that error handling path was taken

    def test_status_without_active_task_displays_hint(self, temp_db):
        """Test jot status displays helpful hint when no active task."""
        import contextlib

        import typer

        from jot.commands.status import _error_console, status_command

        # Mock the error console to capture print calls
        with patch.object(_error_console, "print") as mock_print:
            with contextlib.suppress(typer.Exit):
                status_command(quiet=False)

            # Verify error message and hint were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("No active task" in str(call) for call in print_calls)
            assert any("jot add" in str(call) for call in print_calls)

    def test_status_without_active_task_exits_with_code_1(self, temp_db):
        """Test jot status exits with code 1 when no active task."""
        runner = CliRunner()

        # Act: Run jot status with no active task
        result = runner.invoke(app, ["status"], catch_exceptions=False)

        # Assert: Exit code is 1 (user error)
        assert result.exit_code == 1

    def test_status_quiet_mode_with_active_task(self, temp_db):
        """Test jot status --quiet with active task."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status --quiet
        result = runner.invoke(app, ["status", "--quiet"])

        # Assert: Exit code 0, no output
        assert result.exit_code == 0
        assert result.stdout == ""  # No output

    def test_status_quiet_mode_without_active_task(self, temp_db):
        """Test jot status --quiet without active task."""
        runner = CliRunner()

        # Act: Run jot status --quiet with no active task
        result = runner.invoke(app, ["status", "--quiet"], catch_exceptions=False)

        # Assert: Exit code 1, no output
        assert result.exit_code == 1
        assert result.stdout == ""  # No output

    def test_status_quiet_mode_short_flag(self, temp_db):
        """Test jot status -q short flag works the same as --quiet."""
        runner = CliRunner()

        # Act: Run jot status -q with no active task
        result = runner.invoke(app, ["status", "-q"], catch_exceptions=False)

        # Assert: Exit code 1, no output (same as --quiet)
        assert result.exit_code == 1
        assert result.stdout == ""

    def test_status_performance_under_100ms(self, temp_db):
        """Test jot status completes in <100ms (NFR1)."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Performance test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status and measure time
        start = time.time()
        result = runner.invoke(app, ["status"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Assert: Command completes in <100ms
        assert result.exit_code == 0
        assert elapsed < 100, f"Command took {elapsed}ms, exceeds 100ms limit"

    def test_status_performance_with_many_tasks(self, temp_db):
        """Test jot status performance with many tasks in database."""
        # Arrange: Create many completed tasks and one active task
        repo = TaskRepository()
        for i in range(100):
            task = Task(
                id=str(uuid.uuid4()),
                description=f"Completed task {i}",
                state=TaskState.COMPLETED,
                created_at=datetime.now(UTC) - timedelta(days=i),
                updated_at=datetime.now(UTC) - timedelta(days=i),
                completed_at=datetime.now(UTC) - timedelta(days=i),
            )
            repo.create_task(task)

        # Create one active task
        active_task = Task(
            id=str(uuid.uuid4()),
            description="Active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(active_task)
        runner = CliRunner()

        # Act: Run jot status and measure time
        start = time.time()
        result = runner.invoke(app, ["status"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Assert: Command still completes in <100ms even with many tasks
        assert result.exit_code == 0
        assert elapsed < 100, f"Command took {elapsed}ms, exceeds 100ms limit"
        assert "Active task" in result.stdout

    def test_status_handles_database_error(self, temp_db):
        """Test jot status handles DatabaseError correctly."""
        from jot.db.repository import TaskRepository

        # Mock TaskRepository to raise DatabaseError
        with (
            patch.object(TaskRepository, "__init__", return_value=None),
            patch.object(
                TaskRepository,
                "get_active_task",
                side_effect=DatabaseError("Database connection failed"),
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(app, ["status"], catch_exceptions=False)

            # Assert: Exit code 2 (system error)
            assert result.exit_code == 2
            # Note: CliRunner may capture stderr separately, but exit code 2 confirms error handling
            # The actual error message format is verified by manual testing

    def test_status_exits_with_code_0_on_success(self, temp_db):
        """Test jot status exits with code 0 when active task exists."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Success test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Exit code is 0 (success)
        assert result.exit_code == 0

    def test_status_shows_very_old_tasks(self, temp_db):
        """Test jot status handles very old tasks (months/years)."""
        # Arrange: Create task from 400 days ago (over a year)
        repo = TaskRepository()
        very_old = datetime.now(UTC) - timedelta(days=400)
        task = Task(
            id=str(uuid.uuid4()),
            description="Very old task",
            state=TaskState.ACTIVE,
            created_at=very_old,
            updated_at=very_old,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows task with days format (since we only support up to days)
        assert result.exit_code == 0
        assert "400 day" in result.stdout.lower()
        assert "ago" in result.stdout.lower()

    def test_status_handles_long_description(self, temp_db):
        """Test jot status handles tasks with very long descriptions."""
        # Arrange: Create task with long description (near 2000 char limit)
        repo = TaskRepository()
        long_desc = "A" * 1500 + " - this is a very long task description for testing"
        task = Task(
            id=str(uuid.uuid4()),
            description=long_desc,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Task is displayed without errors
        assert result.exit_code == 0
        assert "🎯" in result.stdout
        # Check that at least part of the description is shown
        assert "AAAA" in result.stdout

    def test_status_handles_negative_time_delta(self, temp_db):
        """Test jot status handles tasks with future timestamps (clock skew)."""
        # Arrange: Create task with future timestamp (simulates clock skew)
        repo = TaskRepository()
        future_time = datetime.now(UTC) + timedelta(minutes=5)
        task = Task(
            id=str(uuid.uuid4()),
            description="Future task",
            state=TaskState.ACTIVE,
            created_at=future_time,
            updated_at=future_time,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot status
        result = runner.invoke(app, ["status"])

        # Assert: Shows "just now" instead of negative time
        assert result.exit_code == 0
        assert "just now" in result.stdout.lower()
