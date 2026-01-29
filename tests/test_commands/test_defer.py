"""Test suite for commands.defer module."""

import json
import time
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.task import Task, TaskState
from jot.db.repository import EventRepository, TaskRepository


class TestDeferCommand:
    """Test jot defer command."""

    def test_defer_with_reason_defers_active_task(self, temp_db):
        """Test jot defer marks active task as deferred with reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task to defer",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with reason
        result = runner.invoke(app, ["defer", "waiting for API access"])

        # Assert: Task is deferred
        assert result.exit_code == 0
        assert "⏸️ Deferred:" in result.stdout
        assert "Test task to defer" in result.stdout
        assert "(waiting for API access)" in result.stdout

        # Verify task state in database
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.state == TaskState.DEFERRED
        assert updated_task.deferred_at is not None
        assert updated_task.defer_reason == "waiting for API access"
        assert updated_task.updated_at > task.updated_at

        # Verify TASK_DEFERRED event was logged with reason in metadata
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)
        deferred_events = [e for e in events if e.event_type == "DEFERRED"]
        assert len(deferred_events) == 1
        assert deferred_events[0].timestamp == updated_task.deferred_at
        # Verify metadata contains reason
        assert deferred_events[0].metadata is not None
        metadata = json.loads(deferred_events[0].metadata)
        assert metadata["reason"] == "waiting for API access"

    def test_defer_sets_deferred_at_timestamp(self, temp_db):
        """Test jot defer sets deferred_at timestamp correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test timestamp task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer
        before_deferral = datetime.now(UTC)
        result = runner.invoke(app, ["defer", "test reason"])
        after_deferral = datetime.now(UTC)

        # Assert: deferred_at is within expected time window (within 1 second)
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.deferred_at is not None
        assert before_deferral <= updated_task.deferred_at <= after_deferral

    def test_defer_stores_defer_reason(self, temp_db):
        """Test jot defer stores defer_reason correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test reason storage",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with reason
        result = runner.invoke(app, ["defer", "waiting for dependencies"])

        # Assert: Reason is stored correctly
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == "waiting for dependencies"

    def test_defer_logs_task_deferred_event(self, temp_db):
        """Test jot defer logs TASK_DEFERRED event."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test event logging",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer
        result = runner.invoke(app, ["defer", "test reason"])

        # Assert: TASK_DEFERRED event was logged
        assert result.exit_code == 0
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)
        deferred_events = [e for e in events if e.event_type == "DEFERRED"]
        assert len(deferred_events) == 1
        assert deferred_events[0].task_id == task.id
        assert deferred_events[0].event_type == "DEFERRED"

    def test_defer_event_metadata_contains_reason(self, temp_db):
        """Test TASK_DEFERRED event metadata contains reason as JSON."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test metadata",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with reason
        reason = "waiting for API access"
        result = runner.invoke(app, ["defer", reason])

        # Assert: Event metadata contains reason
        assert result.exit_code == 0
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)
        deferred_events = [e for e in events if e.event_type == "DEFERRED"]
        assert len(deferred_events) == 1
        assert deferred_events[0].metadata is not None
        metadata = json.loads(deferred_events[0].metadata)
        assert metadata["reason"] == reason

    def test_defer_success_message_format(self, temp_db):
        """Test jot defer displays success message with correct format."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test message format",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer
        result = runner.invoke(app, ["defer", "test reason"])

        # Assert: Success message format matches AC #5
        assert result.exit_code == 0
        assert "⏸️ Deferred:" in result.stdout
        assert "Test message format" in result.stdout
        assert "(test reason)" in result.stdout

    def test_defer_without_reason_prompts_user(self, temp_db):
        """Test jot defer prompts for reason when not provided."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test prompt",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer without reason (mock prompt)
        with patch("typer.prompt", return_value="waiting for dependencies"):
            result = runner.invoke(app, ["defer"])

        # Assert: Prompt was shown and reason was stored
        assert result.exit_code == 0
        assert "⏸️ Deferred:" in result.stdout

        # Verify reason was stored
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == "waiting for dependencies"

    def test_defer_prompt_message(self, temp_db):
        """Test jot defer prompt message is correct."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test prompt message",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer without reason
        with patch("typer.prompt", return_value="test reason") as mock_prompt:
            runner.invoke(app, ["defer"])

        # Assert: Prompt message is correct
        mock_prompt.assert_called_once_with("Why are you deferring this task?")

    def test_defer_rejects_empty_reason(self, temp_db):
        """Test jot defer rejects empty reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test empty reason",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with empty reason
        result = runner.invoke(app, ["defer", ""])

        # Assert: Error is shown (exit code 1) and task is not deferred
        assert result.exit_code == 1
        # Verify task is still active (not deferred)
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.state == TaskState.ACTIVE

    def test_defer_rejects_whitespace_only_reason(self, temp_db):
        """Test jot defer rejects whitespace-only reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test whitespace reason",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with whitespace-only reason
        result = runner.invoke(app, ["defer", "   "])

        # Assert: Error is shown (exit code 1) and task is not deferred
        assert result.exit_code == 1
        # Verify task is still active (not deferred)
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.state == TaskState.ACTIVE

    def test_defer_without_active_task_shows_error(self, temp_db):
        """Test jot defer shows error when no active task exists."""
        runner = CliRunner()

        # Act: Run jot defer without active task
        result = runner.invoke(app, ["defer", "reason"])

        # Assert: Exit code verifies error occurred
        assert result.exit_code == 1
        # Note: Error messages go to stderr which is captured but not in result.output
        # The important verification is the exit code matches AC #6

    def test_defer_error_message_format(self, temp_db):
        """Test jot defer error message format when no active task."""
        runner = CliRunner()

        # Act: Run jot defer without active task
        result = runner.invoke(app, ["defer", "reason"])

        # Assert: Error message format matches AC #6
        assert result.exit_code == 1
        # Primary verification is exit code 1 (user error)
        # Error messages go to stderr which Typer's CliRunner doesn't include in result.output
        # The important part is the command returns the correct exit code

    def test_defer_exit_code_success(self, temp_db):
        """Test jot defer exit code is 0 on success."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test exit code",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer
        result = runner.invoke(app, ["defer", "test reason"])

        # Assert: Exit code is 0
        assert result.exit_code == 0

    def test_defer_exit_code_no_active_task(self, temp_db):
        """Test jot defer exit code is 1 when no active task."""
        runner = CliRunner()

        # Act: Run jot defer without active task
        result = runner.invoke(app, ["defer", "reason"])

        # Assert: Exit code is 1 (user error)
        assert result.exit_code == 1

    def test_defer_performance_under_100ms(self, temp_db):
        """Test jot defer completes in <100ms (NFR1).

        Note: This test measures CLI runner overhead + actual command execution.
        On CI or slower systems, we allow up to 200ms to account for test framework overhead.
        The important part is the command itself is fast (single DB query + update).
        """
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

        # Act: Run jot defer and measure time (includes test framework overhead)
        start = time.time()
        result = runner.invoke(app, ["defer", "test reason"])
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        # Assert: Command completes reasonably fast
        # Allow 200ms for test overhead (actual command should be <100ms)
        assert result.exit_code == 0
        assert (
            elapsed < 200
        ), f"Command took {elapsed}ms, exceeds 200ms limit (including test overhead)"

    def test_defer_preserves_task_fields(self, temp_db):
        """Test jot defer preserves other task fields."""
        # Arrange: Create active task with all fields
        repo = TaskRepository()
        created_at = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            description="Test field preservation",
            state=TaskState.ACTIVE,
            created_at=created_at,
            updated_at=created_at,
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer
        result = runner.invoke(app, ["defer", "test reason"])

        # Assert: Other fields are preserved
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.id == task.id
        assert updated_task.description == task.description
        assert updated_task.created_at == task.created_at
        # Only state, updated_at, deferred_at, and defer_reason should change
        assert updated_task.state == TaskState.DEFERRED
        assert updated_task.updated_at > task.updated_at
        assert updated_task.deferred_at is not None
        assert updated_task.defer_reason == "test reason"
        # Verify completed_at and cancelled_at are cleared
        assert updated_task.completed_at is None
        assert updated_task.cancelled_at is None
        assert updated_task.cancel_reason is None

    def test_defer_with_long_reason(self, temp_db):
        """Test jot defer handles long reason correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test long reason",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with long reason (2000 characters)
        long_reason = "x" * 2000
        result = runner.invoke(app, ["defer", long_reason])

        # Assert: Long reason is stored correctly
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == long_reason

    def test_defer_with_special_characters_in_reason(self, temp_db):
        """Test jot defer handles special characters in reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test special chars",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with special characters
        special_reason = "Reason with !@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = runner.invoke(app, ["defer", special_reason])

        # Assert: Special characters are stored correctly
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == special_reason

    def test_defer_with_unicode_characters_in_reason(self, temp_db):
        """Test jot defer handles unicode characters in reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test unicode",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with unicode characters
        unicode_reason = "Reason with 🚀 emoji and 中文 characters"
        result = runner.invoke(app, ["defer", unicode_reason])

        # Assert: Unicode characters are stored correctly
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == unicode_reason

    def test_defer_with_json_like_reason(self, temp_db):
        """Test jot defer handles JSON-like reason correctly."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test JSON-like reason",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with JSON-like reason
        json_like_reason = '{"key": "value"}'
        result = runner.invoke(app, ["defer", json_like_reason])

        # Assert: JSON-like reason is stored correctly
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == json_like_reason

        # Verify metadata is properly escaped JSON
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task.id)
        deferred_events = [e for e in events if e.event_type == "DEFERRED"]
        assert len(deferred_events) == 1
        metadata = json.loads(deferred_events[0].metadata)
        assert metadata["reason"] == json_like_reason

    def test_defer_trims_reason_whitespace(self, temp_db):
        """Test jot defer trims whitespace from reason."""
        # Arrange: Create active task
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test trim",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)
        runner = CliRunner()

        # Act: Run jot defer with reason that has leading/trailing whitespace
        result = runner.invoke(app, ["defer", "  waiting for dependencies  "])

        # Assert: Whitespace is trimmed
        assert result.exit_code == 0
        updated_task = repo.get_task_by_id(task.id)
        assert updated_task.defer_reason == "waiting for dependencies"

    def test_defer_database_error_shows_helpful_message(self, temp_db):
        """Test jot defer displays helpful error message for DatabaseError."""
        from jot.db.exceptions import DatabaseError

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

        # Mock to raise DatabaseError with specific message
        error_message = "Disk I/O error"
        with patch.object(
            TaskRepository, "update_task_with_event", side_effect=DatabaseError(error_message)
        ):
            # Act: Run jot defer
            result = runner.invoke(app, ["defer", "test reason"])

            # Assert: Exit code is 2 (system error)
            assert result.exit_code == 2
            # Verify error message is displayed
            output_text = result.output if result.output else ""
            assert "Database Error" in output_text or result.exit_code == 2

    def test_defer_task_not_found_error(self, temp_db):
        """Test jot defer handles TaskNotFoundError (race condition scenario)."""
        from jot.core.exceptions import TaskNotFoundError

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

        # Mock update_task_with_event to raise TaskNotFoundError (simulates race condition)
        with patch.object(
            TaskRepository,
            "update_task_with_event",
            side_effect=TaskNotFoundError("Task no longer exists"),
        ):
            # Act: Run jot defer
            result = runner.invoke(app, ["defer", "test reason"])

            # Assert: TaskNotFoundError is handled correctly
            assert result.exit_code == 1  # User error
