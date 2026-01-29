"""End-to-end tests for deferred task management workflow.

Tests the complete workflow: add -> defer -> deferred -> resume
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app
from jot.core.task import Task, TaskState
from jot.db.repository import EventRepository, TaskRepository


class TestDeferredTaskWorkflowE2E:
    """End-to-end tests for deferred task management workflow."""

    def test_full_workflow_defer_deferred_resume(self, temp_db):
        """Test complete workflow: add task -> defer -> list deferred -> resume."""
        runner = CliRunner()
        repo = TaskRepository()
        event_repo = EventRepository()

        # Step 1: Add a task
        result = runner.invoke(app, ["add", "Complete project documentation"])
        assert result.exit_code == 0
        active_task = repo.get_active_task()
        assert active_task is not None
        assert active_task.description == "Complete project documentation"
        task_id = active_task.id

        # Step 2: Defer the task
        result = runner.invoke(app, ["defer", "waiting for API access"])
        assert result.exit_code == 0
        assert "⏸️ Deferred:" in result.stdout
        assert "Complete project documentation" in result.stdout

        # Verify task is deferred
        deferred_task = repo.get_task_by_id(task_id)
        assert deferred_task.state == TaskState.DEFERRED
        assert deferred_task.defer_reason == "waiting for API access"
        assert deferred_task.deferred_at is not None

        # Verify DEFERRED event was created
        events = event_repo.get_events_for_task(task_id)
        deferred_events = [e for e in events if e.event_type == "DEFERRED"]
        assert len(deferred_events) == 1

        # Step 3: List deferred tasks
        result = runner.invoke(app, ["deferred"])
        assert result.exit_code == 0
        assert "Complete project documentation" in result.stdout
        assert "waiting for API access" in result.stdout
        assert "1" in result.stdout  # Task number

        # Step 4: Resume the deferred task
        result = runner.invoke(app, ["resume", "1"])
        assert result.exit_code == 0
        assert "🎯 Resumed: Complete project documentation" in result.stdout

        # Verify task is active again
        resumed_task = repo.get_task_by_id(task_id)
        assert resumed_task.state == TaskState.ACTIVE
        assert resumed_task.deferred_at is None
        assert resumed_task.defer_reason is None

        # Verify RESUMED event was created
        events = event_repo.get_events_for_task(task_id)
        resumed_events = [e for e in events if e.event_type == "RESUMED"]
        assert len(resumed_events) == 1

    def test_workflow_with_multiple_deferred_tasks(self, temp_db):
        """Test workflow with multiple deferred tasks and resume by number."""
        runner = CliRunner()
        repo = TaskRepository()

        # Create and defer first task
        result = runner.invoke(app, ["add", "First task"])
        assert result.exit_code == 0
        _task1_id = repo.get_active_task().id  # noqa: F841 - captured for debugging
        result = runner.invoke(app, ["defer", "reason 1"])
        assert result.exit_code == 0

        # Create and defer second task
        result = runner.invoke(app, ["add", "Second task"])
        assert result.exit_code == 0
        task2_id = repo.get_active_task().id
        result = runner.invoke(app, ["defer", "reason 2"])
        assert result.exit_code == 0

        # List deferred tasks
        result = runner.invoke(app, ["deferred"])
        assert result.exit_code == 0
        assert "First task" in result.stdout
        assert "Second task" in result.stdout

        # Resume second task (newest, should be #2)
        result = runner.invoke(app, ["resume", "2"])
        assert result.exit_code == 0
        assert "🎯 Resumed: Second task" in result.stdout

        # Verify correct task is active
        active_task = repo.get_active_task()
        assert active_task.id == task2_id

    def test_workflow_resume_with_active_task_conflict(self, temp_db):
        """Test workflow where resuming deferred task conflicts with active task."""
        runner = CliRunner()
        repo = TaskRepository()

        # Create and defer a task
        result = runner.invoke(app, ["add", "Task to defer"])
        assert result.exit_code == 0
        deferred_task_id = repo.get_active_task().id
        result = runner.invoke(app, ["defer", "waiting"])
        assert result.exit_code == 0

        # Create new active task
        result = runner.invoke(app, ["add", "Current active task"])
        assert result.exit_code == 0
        active_task_id = repo.get_active_task().id

        # Resume deferred task, choosing to defer current active task
        with patch("typer.prompt", return_value="D"):
            result = runner.invoke(app, ["resume", "1"])

        assert result.exit_code == 0
        assert "🎯 Resumed: Task to defer" in result.stdout

        # Verify original deferred task is now active
        active_task = repo.get_active_task()
        assert active_task.id == deferred_task_id

        # Verify previous active task is now deferred
        previous_active = repo.get_task_by_id(active_task_id)
        assert previous_active.state == TaskState.DEFERRED

    def test_workflow_deferred_list_shows_correct_order(self, temp_db):
        """Test that deferred list shows tasks in correct order (oldest first)."""
        runner = CliRunner()
        repo = TaskRepository()
        now = datetime.now(UTC)

        # Create and defer tasks with different timestamps
        # Task 1: oldest
        task1 = Task(
            id=str(uuid.uuid4()),
            description="Oldest deferred task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now - timedelta(seconds=20),
            defer_reason="reason 1",
        )
        repo.create_task(task1)

        # Task 2: newest
        task2 = Task(
            id=str(uuid.uuid4()),
            description="Newest deferred task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_at=now,
            defer_reason="reason 2",
        )
        repo.create_task(task2)

        # List deferred tasks
        result = runner.invoke(app, ["deferred"])
        assert result.exit_code == 0

        # Verify order: oldest appears first
        oldest_index = result.stdout.find("Oldest deferred task")
        newest_index = result.stdout.find("Newest deferred task")
        assert oldest_index < newest_index

    def test_workflow_resume_preserves_task_history(self, temp_db):
        """Test that resuming a task preserves its event history."""
        runner = CliRunner()
        repo = TaskRepository()
        event_repo = EventRepository()

        # Create task
        result = runner.invoke(app, ["add", "Task with history"])
        assert result.exit_code == 0
        task_id = repo.get_active_task().id

        # Defer task
        result = runner.invoke(app, ["defer", "waiting"])
        assert result.exit_code == 0

        # Verify DEFERRED event exists
        events_before = event_repo.get_events_for_task(task_id)
        deferred_count = len([e for e in events_before if e.event_type == "DEFERRED"])
        assert deferred_count == 1

        # Resume task
        result = runner.invoke(app, ["resume", "1"])
        assert result.exit_code == 0

        # Verify both DEFERRED and RESUMED events exist
        events_after = event_repo.get_events_for_task(task_id)
        event_types = [e.event_type for e in events_after]
        assert "DEFERRED" in event_types
        assert "RESUMED" in event_types
