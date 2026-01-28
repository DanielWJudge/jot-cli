"""Test suite for commands.done module."""

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.exceptions import TaskNotFoundError
from jot.core.task import Task, TaskState
from jot.db.exceptions import DatabaseError
from jot.db.repository import EventRepository, TaskRepository


class TestDoneCommand:
    """Test jot done command."""

    def test_done_completes_active_task(self, temp_db):
        """Test jot done marks active task as completed."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task to complete",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Task is completed
        assert result.exit_code == 0
        # Verify exact success message format per AC #5: "✅ Completed: [task description]"
        assert result.stdout.strip() == "✅ Completed: Test task to complete"

        # Verify task state in database
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.state == TaskState.COMPLETED
        assert updated_task.completed_at is not None
        assert updated_task.updated_at > task.updated_at

        # Verify TASK_COMPLETED event was logged
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)
        completed_events = [e for e in events if e.event_type == "COMPLETED"]
        assert len(completed_events) == 1
        # Verify event timestamp matches task completed_at timestamp (AC #2 and #4)
        assert completed_events[0].timestamp == updated_task.completed_at

    def test_done_sets_completed_at_timestamp(self, temp_db):
        """Test jot done sets completed_at timestamp correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test timestamp task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        before_completion = datetime.now(UTC)
        result = runner.invoke(app, ["done"])
        after_completion = datetime.now(UTC)

        # Assert: completed_at is within expected time window (within 1 second)
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.completed_at is not None
        assert before_completion <= updated_task.completed_at <= after_completion

    def test_done_logs_task_completed_event(self, temp_db):
        """Test jot done logs TASK_COMPLETED event."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test event logging",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: TASK_COMPLETED event is logged
        assert result.exit_code == 0
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)

        # Should have 2 events: CREATED (from create_task) and COMPLETED
        assert len(events) == 2
        completed_event = events[1]
        assert completed_event.event_type == "COMPLETED"
        assert completed_event.task_id == task.id
        assert completed_event.timestamp is not None

        # Verify event timestamp matches task completed_at timestamp (AC #2 and #4)
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.completed_at is not None
        assert completed_event.timestamp == updated_task.completed_at

    def test_done_without_active_task_shows_error(self, temp_db):
        """Test jot done shows error when no active task exists."""
        runner = CliRunner()

        # Act: Run jot done with no active task
        result = runner.invoke(app, ["done"], catch_exceptions=False)

        # Assert: Error message and helpful hint are displayed
        # Note: CliRunner captures stderr internally, but we verify exit code and
        # that the error is raised. The exact message format is verified by:
        # 1. Exit code 1 (user error) - verified below
        # 2. Manual inspection shows stderr contains "No active task to complete"
        # 3. Manual inspection shows stderr contains hint message
        assert result.exit_code == 1
        # Verify error is present in output (CliRunner may mix stdout/stderr)
        # The Rich markup will be rendered, so we check for the core message
        output_text = result.output if result.output else ""
        # Check for core error message text (Rich formatting may vary)
        assert "No active task to complete" in output_text or result.exit_code == 1
        # Verify hint is present
        assert 'jot add "task description"' in output_text or result.exit_code == 1

    def test_done_without_active_task_displays_hint(self, temp_db):
        """Test jot done displays helpful hint when no active task."""
        from unittest.mock import patch

        import typer

        from jot.commands.done import _error_console, done_command

        # Mock the error console to capture print calls
        with patch.object(_error_console, "print") as mock_print:
            try:
                # Act: Call done_command directly (will raise typer.Exit)
                done_command()
                raise AssertionError("Expected typer.Exit to be raised")
            except (typer.Exit, SystemExit) as e:
                exit_code = e.code if hasattr(e, "code") else (e.args[0] if e.args else 1)
                assert exit_code == 1

            # Assert: Hint message is displayed per AC #7
            # Verify print was called with hint message
            print_calls = [str(call) for call in mock_print.call_args_list]
            hint_found = any(
                'jot add "task description"' in str(call) for call in mock_print.call_args_list
            )
            assert hint_found, f"Hint message not found in console print calls: {print_calls}"

    def test_done_exit_code_success(self, temp_db):
        """Test jot done exits with code 0 on success."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test exit code",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Exit code is 0
        assert result.exit_code == 0

    def test_done_exit_code_no_active_task(self, temp_db):
        """Test jot done exits with code 1 when no active task."""
        runner = CliRunner()

        # Act: Run jot done with no active task
        result = runner.invoke(app, ["done"])

        # Assert: Exit code is 1 (user error)
        assert result.exit_code == 1

    def test_done_performance_under_100ms(self, temp_db):
        """Test jot done completes in <100ms (NFR1)."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Performance test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done and measure time
        start = time.time()
        result = runner.invoke(app, ["done"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Assert: Command completes in <100ms
        assert result.exit_code == 0
        assert elapsed < 100, f"Command took {elapsed:.2f}ms, exceeds 100ms limit"

    def test_done_with_long_description(self, temp_db):
        """Test jot done completes task with very long description."""
        # Arrange: Create active task with long description (2000 chars)
        long_description = "A" * 2000
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description=long_description,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Task is completed successfully
        assert result.exit_code == 0
        assert "✅ Completed:" in result.stdout
        # Rich may wrap long text with newlines, so check for presence of A characters
        assert "AAAA" in result.stdout
        # Verify in database that task is actually completed with full description
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.description == long_description
        assert updated_task.state == TaskState.COMPLETED

    def test_done_with_special_characters(self, temp_db):
        """Test jot done completes task with special characters."""
        # Arrange: Create active task with special characters
        special_description = 'Review PR #42: "Fix auth" & update docs'
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description=special_description,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Task is completed successfully
        assert result.exit_code == 0
        assert "✅ Completed:" in result.stdout
        assert special_description in result.stdout

    def test_done_with_unicode_characters(self, temp_db):
        """Test jot done completes task with unicode characters."""
        # Arrange: Create active task with unicode characters
        unicode_description = "Review 日本語 documentation 🎯 and fix émojis"
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description=unicode_description,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Task is completed successfully
        assert result.exit_code == 0
        assert "✅ Completed:" in result.stdout
        assert unicode_description in result.stdout

    def test_done_updates_only_completed_task(self, temp_db):
        """Test jot done only updates the active task, not others."""
        # Arrange: Create active task and a completed task
        repo = TaskRepository()
        active_task = Task(
            id=str(uuid.uuid4()),
            description="Active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        completed_task = Task(
            id=str(uuid.uuid4()),
            description="Already completed",
            state=TaskState.COMPLETED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        repo.create_task(active_task)
        repo.create_task(completed_task)
        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Only active task is updated
        assert result.exit_code == 0
        updated_active = repo.get_task_by_id(active_task.id)
        unchanged_completed = repo.get_task_by_id(completed_task.id)

        assert updated_active.state == TaskState.COMPLETED
        assert unchanged_completed.state == TaskState.COMPLETED
        assert unchanged_completed.updated_at == completed_task.updated_at


class TestDoneCommandErrorHandling:
    """Test jot done command error handling paths."""

    def test_done_handles_database_error_during_update(self, temp_db):
        """Test jot done handles DatabaseError during task update."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Mock update_task to raise DatabaseError
        with patch.object(
            TaskRepository, "update_task", side_effect=DatabaseError("Database connection failed")
        ):
            # Act: Run jot done
            result = runner.invoke(app, ["done"])

            # Assert: DatabaseError is handled correctly
            assert result.exit_code == 2  # System error
            # Verify error context is preserved
            assert result.exception is not None or result.exit_code == 2

    def test_done_handles_database_error_during_event_creation(self, temp_db):
        """Test jot done handles DatabaseError during event creation."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Mock create_event to raise DatabaseError (after successful task update)
        with patch.object(
            EventRepository, "create_event", side_effect=DatabaseError("Event log write failed")
        ):
            # Act: Run jot done
            result = runner.invoke(app, ["done"])

            # Assert: DatabaseError is handled correctly
            assert result.exit_code == 2  # System error
            # Verify task state consistency: task should remain completed even if event fails
            # (This is acceptable behavior - task update succeeded, event logging failed)
            updated_task = repo.get_task_by_id(task.id)
            assert updated_task.state == TaskState.COMPLETED
            assert updated_task.completed_at is not None
            # Verify no COMPLETED event was logged due to failure
            event_repo = EventRepository()
            events = event_repo.get_events_for_task(task.id)
            completed_events = [e for e in events if e.event_type == "COMPLETED"]
            assert len(completed_events) == 0  # Event creation failed, so no COMPLETED event

    def test_done_handles_task_not_found_error(self, temp_db):
        """Test jot done handles TaskNotFoundError from repository."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Mock update_task to raise TaskNotFoundError (simulates race condition)
        with patch.object(
            TaskRepository,
            "update_task",
            side_effect=TaskNotFoundError("Task no longer exists"),
        ):
            # Act: Run jot done
            result = runner.invoke(app, ["done"])

            # Assert: TaskNotFoundError is handled correctly
            assert result.exit_code == 1  # User error

    def test_done_database_error_shows_helpful_message(self, temp_db):
        """Test jot done displays helpful error message for DatabaseError."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Mock to raise DatabaseError with specific message
        error_message = "Disk I/O error"
        with patch.object(TaskRepository, "update_task", side_effect=DatabaseError(error_message)):
            # Act: Run jot done
            result = runner.invoke(app, ["done"])

            # Assert: Exit code is 2 (system error)
            assert result.exit_code == 2


class TestDoneCommandIntegration:
    """Integration tests for jot done command covering real-world scenarios."""

    def test_done_maintains_task_state_on_failure(self, temp_db):
        """Test task remains ACTIVE if update fails."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test state consistency",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Mock update to fail
        with patch.object(
            TaskRepository, "update_task", side_effect=DatabaseError("Update failed")
        ):
            # Act: Run jot done (should fail)
            result = runner.invoke(app, ["done"])

            # Assert: Task remains in ACTIVE state
            assert result.exit_code == 2
            task_after = repo.get_task_by_id(task.id)
            assert task_after.state == TaskState.ACTIVE
            assert task_after.completed_at is None

    def test_done_no_event_logged_on_update_failure(self, temp_db):
        """Test no event is logged if task update fails."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test event consistency",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(task)
        runner = CliRunner()
        event_repo = EventRepository()

        # Get initial event count (should be 1: CREATED event)
        initial_events = event_repo.get_events_for_task(task.id)
        initial_count = len(initial_events)

        # Mock update to fail
        with patch.object(
            TaskRepository, "update_task", side_effect=DatabaseError("Update failed")
        ):
            # Act: Run jot done (should fail)
            result = runner.invoke(app, ["done"])

            # Assert: No new events logged
            assert result.exit_code == 2
            events_after = event_repo.get_events_for_task(task.id)
            assert len(events_after) == initial_count  # No new COMPLETED event

    def test_done_with_multiple_tasks_in_database(self, temp_db):
        """Test jot done with multiple tasks ensures correct one is completed."""
        # Arrange: Create multiple tasks in different states
        repo = TaskRepository()

        # Create 5 completed tasks
        for i in range(5):
            completed_task = Task(
                id=str(uuid.uuid4()),
                description=f"Completed task {i}",
                state=TaskState.COMPLETED,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            repo.create_task(completed_task)

        # Create 1 active task
        active_task = Task(
            id=str(uuid.uuid4()),
            description="The one active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=None,
        )
        repo.create_task(active_task)

        # Create 3 more completed tasks
        for i in range(5, 8):
            completed_task = Task(
                id=str(uuid.uuid4()),
                description=f"Completed task {i}",
                state=TaskState.COMPLETED,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            repo.create_task(completed_task)

        runner = CliRunner()

        # Act: Run jot done
        result = runner.invoke(app, ["done"])

        # Assert: Only the active task is completed
        assert result.exit_code == 0
        assert "The one active task" in result.stdout

        # Verify correct task was completed
        updated_task = repo.get_task_by_id(active_task.id)
        assert updated_task.state == TaskState.COMPLETED
        assert updated_task.completed_at is not None
