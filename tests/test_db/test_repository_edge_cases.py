"""Edge case tests for repository operations.

This module tests edge cases and advanced scenarios for TaskRepository
and EventRepository that go beyond basic CRUD operations.
"""

import uuid
from datetime import UTC, datetime

from jot.core.task import Task, TaskEvent, TaskState
from jot.db.repository import EventRepository, TaskRepository


class TestTaskRepositoryEdgeCases:
    """Test edge cases for TaskRepository."""

    def test_multiple_tasks_different_states(self, temp_db):
        """Test repository correctly handles multiple tasks with different states."""
        repo = TaskRepository()
        now = datetime.now(UTC)

        # Create tasks in each state
        states_and_ids = []
        for state in [
            TaskState.ACTIVE,
            TaskState.COMPLETED,
            TaskState.CANCELLED,
            TaskState.DEFERRED,
        ]:
            task_id = str(uuid.uuid4())
            task = Task(
                id=task_id,
                description=f"Task in {state.value} state",
                state=state,
                created_at=now,
                updated_at=now,
                completed_at=now if state == TaskState.COMPLETED else None,
                deferred_until=now if state == TaskState.DEFERRED else None,
            )
            repo.create_task(task)
            states_and_ids.append((state, task_id))

        # Verify all tasks can be retrieved correctly
        for state, task_id in states_and_ids:
            retrieved = repo.get_task_by_id(task_id)
            assert retrieved.state == state
            assert task_id in retrieved.id

    def test_get_active_task_with_multiple_completed(self, temp_db):
        """Test get_active_task works correctly among many completed tasks."""
        repo = TaskRepository()
        now = datetime.now(UTC)

        # Create 50 completed tasks
        for i in range(50):
            task = Task(
                id=str(uuid.uuid4()),
                description=f"Completed task {i}",
                state=TaskState.COMPLETED,
                created_at=now,
                updated_at=now,
                completed_at=now,
            )
            repo.create_task(task)

        # Create one active task
        active_id = str(uuid.uuid4())
        active_task = Task(
            id=active_id,
            description="The one active task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(active_task)

        # Verify get_active_task returns the correct one
        active = repo.get_active_task()
        assert active is not None
        assert active.id == active_id

    def test_task_lifecycle_full_workflow(self, temp_db):
        """Test complete task lifecycle: create → update → retrieve."""
        repo = TaskRepository()
        task_id = str(uuid.uuid4())

        # Create task
        created_time = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="New task",
            state=TaskState.ACTIVE,
            created_at=created_time,
            updated_at=created_time,
        )
        repo.create_task(task)

        # Verify creation
        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.state == TaskState.ACTIVE
        assert retrieved.description == "New task"
        assert retrieved.created_at == created_time

        # Update to completed
        completed_time = datetime.now(UTC)
        updated_task = Task(
            id=task_id,
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=created_time,  # Should not change
            updated_at=completed_time,
            completed_at=completed_time,
        )
        repo.update_task(updated_task)

        # Verify update
        final = repo.get_task_by_id(task_id)
        assert final.state == TaskState.COMPLETED
        assert final.description == "Completed task"
        assert final.created_at == created_time  # Should remain unchanged
        assert final.updated_at == completed_time
        assert final.completed_at == completed_time

    def test_update_task_state_transitions(self, temp_db):
        """Test various state transitions through update_task."""
        repo = TaskRepository()
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Create active task
        task = Task(
            id=task_id,
            description="Task for state transitions",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Test ACTIVE → DEFERRED transition
        later = datetime.now(UTC)
        deferred_task = Task(
            id=task_id,
            description="Task for state transitions",
            state=TaskState.DEFERRED,
            created_at=now,
            updated_at=later,
            deferred_until=later,
        )
        repo.update_task(deferred_task)

        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.state == TaskState.DEFERRED
        assert retrieved.deferred_until is not None

        # Test DEFERRED → ACTIVE transition (reactivation)
        reactivated_time = datetime.now(UTC)
        reactivated_task = Task(
            id=task_id,
            description="Task for state transitions",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=reactivated_time,
            deferred_until=None,  # Clear deferred_until
        )
        repo.update_task(reactivated_task)

        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.state == TaskState.ACTIVE
        assert retrieved.deferred_until is None

    def test_repository_operations_are_isolated(self, temp_db):
        """Test that repository operations don't interfere with each other."""
        repo = TaskRepository()
        now = datetime.now(UTC)

        # Create first task
        task1_id = str(uuid.uuid4())
        task1 = Task(
            id=task1_id,
            description="First task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task1)

        # Create second task
        task2_id = str(uuid.uuid4())
        task2 = Task(
            id=task2_id,
            description="Second task",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )
        repo.create_task(task2)

        # Update first task
        updated_task1 = Task(
            id=task1_id,
            description="First task updated",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=datetime.now(UTC),
        )
        repo.update_task(updated_task1)

        # Verify first task was updated but second task was not affected
        retrieved1 = repo.get_task_by_id(task1_id)
        retrieved2 = repo.get_task_by_id(task2_id)

        assert retrieved1.description == "First task updated"
        assert retrieved2.description == "Second task"  # Should be unchanged


class TestEventRepositoryEdgeCases:
    """Test edge cases for EventRepository."""

    def test_create_multiple_events_for_same_task(self, temp_db):
        """Test creating multiple events for the same task."""
        task_repo = TaskRepository()
        event_repo = EventRepository()

        # Create task
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Task with many events",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Create multiple additional events (using valid event types from schema)
        additional_event_types = ["DEFERRED", "COMPLETED", "CANCELLED"]
        for event_type in additional_event_types:
            event = TaskEvent(
                id=0,  # Auto-assigned
                task_id=task_id,
                event_type=event_type,
                timestamp=datetime.now(UTC),
            )
            event_repo.create_event(event)

        # Verify all events are stored
        events = event_repo.get_events_for_task(task_id)
        # Should have CREATED (from create_task) + 3 additional events
        assert len(events) >= 4

        retrieved_event_types = [e.event_type for e in events]
        assert "CREATED" in retrieved_event_types
        for event_type in additional_event_types:
            assert event_type in retrieved_event_types

    def test_events_with_large_metadata(self, temp_db):
        """Test storing events with large JSON metadata."""
        task_repo = TaskRepository()
        event_repo = EventRepository()

        # Create task
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Task with large metadata event",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        task_repo.create_task(task)

        # Create event with large metadata
        large_metadata = '{"reason": "' + ("x" * 1000) + '", "details": "Large payload"}'
        event = TaskEvent(
            id=0,
            task_id=task_id,
            event_type="CANCELLED",
            timestamp=datetime.now(UTC),
            metadata=large_metadata,
        )
        event_repo.create_event(event)

        # Verify metadata is stored correctly
        events = event_repo.get_events_for_task(task_id)
        cancelled_events = [e for e in events if e.event_type == "CANCELLED"]
        assert len(cancelled_events) == 1
        assert len(cancelled_events[0].metadata) > 1000

    def test_events_maintain_insertion_order(self, temp_db):
        """Test that events are returned in timestamp order even if inserted out of order."""
        task_repo = TaskRepository()
        event_repo = EventRepository()

        # Create task
        task_id = str(uuid.uuid4())
        base_time = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Task for ordering test",
            state=TaskState.ACTIVE,
            created_at=base_time,
            updated_at=base_time,
        )
        task_repo.create_task(task)

        # Create events with specific timestamps in non-sequential order
        # Using valid event types: CANCELLED (timestamp 3), DEFERRED (timestamp 1), COMPLETED (timestamp 2)
        from datetime import timedelta

        event1 = TaskEvent(
            id=0,
            task_id=task_id,
            event_type="CANCELLED",
            timestamp=base_time + timedelta(seconds=3),
        )
        event2 = TaskEvent(
            id=0,
            task_id=task_id,
            event_type="DEFERRED",
            timestamp=base_time + timedelta(seconds=1),
        )
        event3 = TaskEvent(
            id=0,
            task_id=task_id,
            event_type="COMPLETED",
            timestamp=base_time + timedelta(seconds=2),
        )

        # Insert in non-chronological order (3, 1, 2)
        event_repo.create_event(event1)
        event_repo.create_event(event2)
        event_repo.create_event(event3)

        # Verify events are returned in timestamp order
        events = event_repo.get_events_for_task(task_id)
        # Should have CREATED (base_time), DEFERRED (+1s), COMPLETED (+2s), CANCELLED (+3s)

        assert len(events) >= 4
        # Verify chronological ordering by timestamp
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp

        # Verify specific ordering of our test events (after CREATED)
        test_events = [e for e in events if e.event_type != "CREATED"]
        assert test_events[0].event_type == "DEFERRED"  # +1s
        assert test_events[1].event_type == "COMPLETED"  # +2s
        assert test_events[2].event_type == "CANCELLED"  # +3s


class TestRepositoryDataIntegrity:
    """Test data integrity and consistency in repository operations."""

    def test_iso_8601_timestamp_roundtrip(self, temp_db):
        """Test that timestamps are stored and retrieved correctly in ISO 8601 format."""
        repo = TaskRepository()

        # Create task with precise timestamp
        task_id = str(uuid.uuid4())
        created_time = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Timestamp roundtrip test",
            state=TaskState.ACTIVE,
            created_at=created_time,
            updated_at=created_time,
        )
        repo.create_task(task)

        # Retrieve and verify timestamp precision
        retrieved = repo.get_task_by_id(task_id)

        # Timestamps should match (within microsecond precision)
        assert retrieved.created_at == created_time
        assert retrieved.updated_at == created_time
        assert retrieved.created_at.tzinfo is not None  # Should have timezone info

    def test_unicode_and_special_chars_in_description(self, temp_db):
        """Test repository handles unicode and special characters correctly."""
        repo = TaskRepository()

        task_id = str(uuid.uuid4())
        unicode_desc = "Task with émojis 🚀 and spëcial çhars: <>&\"'\\n\\t"
        now = datetime.now(UTC)

        task = Task(
            id=task_id,
            description=unicode_desc,
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Verify unicode and special characters are preserved
        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.description == unicode_desc

    def test_null_optional_fields_stored_correctly(self, temp_db):
        """Test that NULL values for optional fields are stored and retrieved correctly."""
        repo = TaskRepository()

        # Create task with all optional fields as None
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Task with no optional fields",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
            completed_at=None,  # Explicitly None
            deferred_until=None,  # Explicitly None
        )
        repo.create_task(task)

        # Retrieve and verify NULL fields
        retrieved = repo.get_task_by_id(task_id)
        assert retrieved.completed_at is None
        assert retrieved.deferred_until is None

        # Update to add optional fields
        later = datetime.now(UTC)
        updated_task = Task(
            id=task_id,
            description="Task with no optional fields",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=later,
            completed_at=later,
            deferred_until=None,  # Still None
        )
        repo.update_task(updated_task)

        # Verify optional field was added
        final = repo.get_task_by_id(task_id)
        assert final.completed_at == later
        assert final.deferred_until is None
