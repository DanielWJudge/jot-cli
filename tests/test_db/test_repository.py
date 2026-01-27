"""Test suite for db.repository module."""

import sqlite3
import uuid
from datetime import UTC, datetime

import pytest

from jot.core.exceptions import TaskNotFoundError
from jot.core.task import Task, TaskEvent, TaskState
from jot.db.repository import EventRepository, TaskRepository


class TestTaskRepository:
    """Test TaskRepository CRUD operations."""

    def test_create_task_creates_task_and_event(self, temp_db):
        """Test create_task() creates both task and CREATED event atomically."""
        repo = TaskRepository()
        event_repo = EventRepository()

        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        repo.create_task(task)

        # Verify task was created
        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.id == task_id
        assert retrieved.description == "Test task"
        assert retrieved.state == TaskState.ACTIVE

        # Verify CREATED event was created
        events = event_repo.get_events_for_task(task_id)
        assert len(events) == 1
        assert events[0].event_type == "CREATED"
        assert events[0].task_id == task_id

    def test_get_task_by_id_returns_task(self, temp_db):
        """Test get_task_by_id() returns the correct task."""
        repo = TaskRepository()

        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Retrieve this task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        retrieved = repo.get_task_by_id(task_id)

        assert retrieved.id == task_id
        assert retrieved.description == "Retrieve this task"
        assert retrieved.state == TaskState.ACTIVE
        assert retrieved.created_at == now
        assert retrieved.updated_at == now

    def test_get_task_by_id_raises_not_found_error(self, temp_db):
        """Test get_task_by_id() raises TaskNotFoundError for missing task."""
        repo = TaskRepository()

        with pytest.raises(TaskNotFoundError) as exc_info:
            repo.get_task_by_id("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)

    def test_get_active_task_returns_active_task(self, temp_db):
        """Test get_active_task() returns the active task."""
        repo = TaskRepository()

        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Active task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        active = repo.get_active_task()

        assert active is not None
        assert active.id == task_id
        assert active.state == TaskState.ACTIVE
        assert active.description == "Active task"

    def test_get_active_task_returns_none_when_no_active(self, temp_db):
        """Test get_active_task() returns None when no active task."""
        repo = TaskRepository()

        active = repo.get_active_task()

        assert active is None

    def test_get_active_task_returns_only_active_state(self, temp_db):
        """Test get_active_task() ignores completed/cancelled/deferred tasks."""
        repo = TaskRepository()

        # Create a completed task
        completed_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        completed_task = Task(
            id=completed_id,
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )
        repo.create_task(completed_task)

        # Should return None since no active task exists
        active = repo.get_active_task()
        assert active is None

        # Create an active task
        active_id = str(uuid.uuid4())
        active_task = Task(
            id=active_id,
            description="Active task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(active_task)

        # Should now return the active task
        active = repo.get_active_task()
        assert active is not None
        assert active.id == active_id
        assert active.state == TaskState.ACTIVE

    def test_update_task_updates_fields(self, temp_db):
        """Test update_task() updates task fields."""
        repo = TaskRepository()

        # Create initial task
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Original description",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Update task
        later = datetime.now(UTC)
        updated_task = Task(
            id=task_id,
            description="Updated description",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=later,
            completed_at=later,
        )
        repo.update_task(updated_task)

        # Verify update
        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.description == "Updated description"
        assert retrieved.state == TaskState.COMPLETED
        assert retrieved.completed_at == later

    def test_update_task_raises_not_found_for_nonexistent_task(self, temp_db):
        """Test update_task() raises TaskNotFoundError for nonexistent task."""
        repo = TaskRepository()

        nonexistent_task = Task(
            id="nonexistent-id",
            description="Does not exist",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with pytest.raises(TaskNotFoundError):
            repo.update_task(nonexistent_task)

    def test_returns_pydantic_models_not_raw_rows(self, temp_db):
        """Test repository methods return Pydantic models, not raw SQLite rows."""
        repo = TaskRepository()

        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Verify get_task_by_id returns Task model
        retrieved = repo.get_task_by_id(task_id)
        assert isinstance(retrieved, Task)
        assert not isinstance(retrieved, sqlite3.Row)

        # Verify get_active_task returns Task model
        active = repo.get_active_task()
        assert isinstance(active, Task)
        assert not isinstance(active, sqlite3.Row)

    def test_handles_optional_timestamp_fields(self, temp_db):
        """Test repository correctly handles optional completed_at and deferred_until."""
        repo = TaskRepository()

        # Create completed task with completed_at
        completed_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        completed_task = Task(
            id=completed_id,
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )
        repo.create_task(completed_task)

        # Create deferred task with deferred_until
        deferred_id = str(uuid.uuid4())
        later = datetime.now(UTC)
        deferred_task = Task(
            id=deferred_id,
            description="Deferred task",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=now,
            deferred_until=later,
        )
        repo.create_task(deferred_task)

        # Verify completed_at is stored and retrieved
        completed = repo.get_task_by_id(completed_id)
        assert completed.completed_at is not None
        assert completed.completed_at == now
        assert completed.deferred_until is None

        # Verify deferred_until is stored and retrieved
        deferred = repo.get_task_by_id(deferred_id)
        assert deferred.deferred_until is not None
        assert deferred.deferred_until == later
        assert deferred.completed_at is None

    def test_handles_special_characters_in_description(self, temp_db):
        """Test repository handles special characters in task description."""
        repo = TaskRepository()

        task_id = str(uuid.uuid4())
        special_desc = "Review PR #123 & update docs (see: https://example.com)"
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description=special_desc,
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.description == special_desc


class TestEventRepository:
    """Test EventRepository operations."""

    def test_create_event_creates_event(self, temp_db):
        """Test create_event() creates event successfully."""
        # First create a task
        task_repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Create additional event
        event_repo = EventRepository()
        later = datetime.now(UTC)
        event = TaskEvent(
            id=0,  # Will be auto-assigned by database
            task_id=task_id,
            event_type="COMPLETED",
            timestamp=later,
        )
        event_repo.create_event(event)

        # Verify event was created
        events = event_repo.get_events_for_task(task_id)
        # Should have 2 events: CREATED (from create_task) and COMPLETED
        assert len(events) >= 2
        assert any(e.event_type == "COMPLETED" for e in events)

    def test_create_event_with_metadata(self, temp_db):
        """Test create_event() stores metadata."""
        # First create a task
        task_repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Create event with metadata
        event_repo = EventRepository()
        metadata = '{"reason": "Not needed anymore"}'
        event = TaskEvent(
            id=0,
            task_id=task_id,
            event_type="CANCELLED",
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )
        event_repo.create_event(event)

        # Verify metadata was stored
        events = event_repo.get_events_for_task(task_id)
        cancelled_events = [e for e in events if e.event_type == "CANCELLED"]
        assert len(cancelled_events) == 1
        assert cancelled_events[0].metadata == metadata

    def test_get_events_for_task_returns_all_events(self, temp_db):
        """Test get_events_for_task() returns all events for a task."""
        # Create task (creates CREATED event)
        task_repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Create additional events
        event_repo = EventRepository()
        for event_type in ["COMPLETED", "CANCELLED"]:
            event = TaskEvent(
                id=0,
                task_id=task_id,
                event_type=event_type,
                timestamp=datetime.now(UTC),
            )
            event_repo.create_event(event)

        # Verify all events are returned
        events = event_repo.get_events_for_task(task_id)
        assert len(events) >= 3
        event_types = [e.event_type for e in events]
        assert "CREATED" in event_types
        assert "COMPLETED" in event_types
        assert "CANCELLED" in event_types

    def test_get_events_for_task_returns_empty_for_nonexistent_task(self, temp_db):
        """Test get_events_for_task() returns empty list for nonexistent task."""
        event_repo = EventRepository()

        events = event_repo.get_events_for_task("nonexistent-id")

        assert events == []

    def test_get_events_for_task_orders_by_timestamp(self, temp_db):
        """Test get_events_for_task() returns events ordered by timestamp."""
        # Create task
        task_repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Get events
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task_id)

        # Verify events are ordered by timestamp
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp

    def test_returns_pydantic_models_not_raw_rows(self, temp_db):
        """Test EventRepository returns Pydantic models, not raw SQLite rows."""
        # Create task
        task_repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Get events
        event_repo = EventRepository()
        events = event_repo.get_events_for_task(task_id)

        # Verify all events are TaskEvent models
        assert len(events) > 0
        for event in events:
            assert isinstance(event, TaskEvent)
            assert not isinstance(event, sqlite3.Row)
