"""Test suite for commands.deferred module."""

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.task import Task, TaskState
from jot.db.repository import TaskRepository


class TestDeferredCommand:
    """Test jot deferred command."""

    def test_deferred_displays_all_tasks(self, temp_db):
        """Test jot deferred displays all deferred tasks."""
        # Arrange: Create multiple deferred tasks
        repo = TaskRepository()
        now = datetime.now(UTC)
        task1 = Task(
            id=str(uuid.uuid4()),
            description="Task 1",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason 1",
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            description="Task 2",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason 2",
        )
        repo.create_task(task1)
        repo.create_task(task2)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Tasks are displayed
        assert result.exit_code == 0
        assert "Task 1" in result.stdout
        assert "Task 2" in result.stdout
        assert "reason 1" in result.stdout
        assert "reason 2" in result.stdout

    def test_deferred_shows_empty_state(self, temp_db):
        """Test jot deferred shows empty state when no deferred tasks."""
        runner = CliRunner()

        result = runner.invoke(app, ["deferred"])

        assert result.exit_code == 0
        assert "No deferred tasks" in result.stdout

    def test_deferred_displays_task_numbers(self, temp_db):
        """Test jot deferred displays tasks with numbers."""
        # Arrange: Create deferred tasks
        repo = TaskRepository()
        now = datetime.now(UTC)
        task1 = Task(
            id=str(uuid.uuid4()),
            description="First task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason",
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            description="Second task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason",
        )
        repo.create_task(task1)
        repo.create_task(task2)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Tasks are numbered
        assert result.exit_code == 0
        assert "1" in result.stdout
        assert "2" in result.stdout

    def test_deferred_shows_description_date_reason(self, temp_db):
        """Test deferred task display shows description, date, reason."""
        # Arrange: Create deferred task
        repo = TaskRepository()
        now = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task description",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="waiting for API",
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: All fields are displayed
        assert result.exit_code == 0
        assert "Test task description" in result.stdout
        assert "waiting for API" in result.stdout
        # Date should be displayed (Today, Yesterday, or formatted date)
        assert (
            "Today" in result.stdout or "Yesterday" in result.stdout or "days ago" in result.stdout
        )

    def test_deferred_orders_by_deferred_at_oldest_first(self, temp_db):
        """Test deferred tasks are ordered by deferred_at (oldest first)."""
        # Arrange: Create deferred tasks with different timestamps
        repo = TaskRepository()
        base_time = datetime.now(UTC)
        task1 = Task(
            id=str(uuid.uuid4()),
            description="Oldest",
            state=TaskState.DEFERRED,
            created_at=base_time,
            updated_at=base_time,
            deferred_at=base_time - timedelta(seconds=10),  # Oldest
            defer_reason="reason",
        )
        task2 = Task(
            id=str(uuid.uuid4()),
            description="Newest",
            state=TaskState.DEFERRED,
            created_at=base_time,
            updated_at=base_time,
            deferred_at=base_time,  # Newer
            defer_reason="reason",
        )
        repo.create_task(task1)
        repo.create_task(task2)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Oldest task appears first
        assert result.exit_code == 0
        oldest_index = result.stdout.find("Oldest")
        newest_index = result.stdout.find("Newest")
        assert oldest_index < newest_index

    def test_deferred_handles_no_reason(self, temp_db):
        """Test deferred task display handles missing reason."""
        # Arrange: Create deferred task without reason
        repo = TaskRepository()
        now = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            description="Task without reason",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Shows "No reason provided"
        assert result.exit_code == 0
        assert "No reason provided" in result.stdout

    def test_deferred_performance_under_100ms(self, temp_db):
        """Test jot deferred completes in <100ms (NFR1)."""
        # Arrange: Create multiple deferred tasks
        repo = TaskRepository()
        now = datetime.now(UTC)
        for i in range(10):
            task = Task(
                id=str(uuid.uuid4()),
                description=f"Task {i}",
                state=TaskState.DEFERRED,
                created_at=now,
                updated_at=now,
                deferred_at=now,
                defer_reason=f"reason {i}",
            )
            repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred and measure time
        start = time.time()
        result = runner.invoke(app, ["deferred"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Assert: Command completes within NFR1 requirement (100ms + 50ms test overhead)
        assert result.exit_code == 0
        assert (
            elapsed < 150
        ), f"Command took {elapsed}ms, exceeds 150ms limit (NFR1: 100ms + 50ms test overhead)"

    def test_deferred_handles_database_error(self, temp_db):
        """Test jot deferred handles DatabaseError gracefully."""
        from jot.db.exceptions import DatabaseError

        runner = CliRunner()

        # Mock TaskRepository.get_deferred_tasks to raise DatabaseError
        with patch.object(
            TaskRepository, "get_deferred_tasks", side_effect=DatabaseError("Database error")
        ):
            result = runner.invoke(app, ["deferred"])

            # Assert: Exit code is 2 (system error)
            assert result.exit_code == 2

    def test_deferred_formats_date_today(self, temp_db):
        """Test deferred date formatting shows 'Today' for today's tasks."""
        # Arrange: Create deferred task deferred today
        repo = TaskRepository()
        now = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            description="Today's task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason",
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Shows "Today"
        assert result.exit_code == 0
        assert "Today" in result.stdout

    def test_deferred_formats_date_yesterday(self, temp_db):
        """Test deferred date formatting shows 'Yesterday' for yesterday's tasks."""
        # Arrange: Create deferred task deferred yesterday
        repo = TaskRepository()
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        task = Task(
            id=str(uuid.uuid4()),
            description="Yesterday's task",
            state=TaskState.DEFERRED,
            created_at=yesterday,
            updated_at=yesterday,
            deferred_at=yesterday,
            defer_reason="reason",
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Shows "Yesterday"
        assert result.exit_code == 0
        assert "Yesterday" in result.stdout

    def test_deferred_formats_date_days_ago(self, temp_db):
        """Test deferred date formatting shows 'X days ago' for recent tasks."""
        # Arrange: Create deferred task deferred 3 days ago
        repo = TaskRepository()
        now = datetime.now(UTC)
        three_days_ago = now - timedelta(days=3)
        task = Task(
            id=str(uuid.uuid4()),
            description="3 days ago task",
            state=TaskState.DEFERRED,
            created_at=three_days_ago,
            updated_at=three_days_ago,
            deferred_at=three_days_ago,
            defer_reason="reason",
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Shows "3 days ago"
        assert result.exit_code == 0
        assert "3 days ago" in result.stdout

    def test_deferred_ignores_non_deferred_tasks(self, temp_db):
        """Test jot deferred only shows deferred tasks, not active/completed/cancelled."""
        # Arrange: Create tasks in different states
        repo = TaskRepository()
        now = datetime.now(UTC)
        active_task = Task(
            id=str(uuid.uuid4()),
            description="Active task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        completed_task = Task(
            id=str(uuid.uuid4()),
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )
        deferred_task = Task(
            id=str(uuid.uuid4()),
            description="Deferred task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason",
        )
        repo.create_task(active_task)
        repo.create_task(completed_task)
        repo.create_task(deferred_task)
        runner = CliRunner()

        # Act: Run jot deferred
        result = runner.invoke(app, ["deferred"])

        # Assert: Only deferred task is shown
        assert result.exit_code == 0
        assert "Deferred task" in result.stdout
        assert "Active task" not in result.stdout
        assert "Completed task" not in result.stdout
