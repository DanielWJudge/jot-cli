"""Test suite for core.task module."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from jot.core.task import Task, TaskEvent, TaskState


class TestTaskState:
    """Test TaskState enum."""

    def test_has_all_states(self):
        """Test enum has all required state values."""
        assert TaskState.ACTIVE == "active"
        assert TaskState.COMPLETED == "completed"
        assert TaskState.CANCELLED == "cancelled"
        assert TaskState.DEFERRED == "deferred"

    def test_enum_values_are_strings(self):
        """Test enum values are strings for database compatibility."""
        assert isinstance(TaskState.ACTIVE.value, str)
        assert isinstance(TaskState.COMPLETED.value, str)


class TestTask:
    """Test Task domain model."""

    def test_creates_task_with_valid_data(self):
        """Test Task model accepts valid data."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        assert task.id == task_id
        assert task.description == "Test task"
        assert task.state == TaskState.ACTIVE
        assert task.created_at == now
        assert task.updated_at == now
        assert task.completed_at is None
        assert task.deferred_until is None

    def test_creates_task_with_optional_fields(self):
        """Test Task model accepts optional completed_at and deferred_until."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        completed_time = datetime.now(UTC)

        task = Task(
            id=task_id,
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=now,
            updated_at=now,
            completed_at=completed_time,
        )

        assert task.completed_at == completed_time
        assert task.deferred_until is None

    def test_rejects_invalid_state(self):
        """Test Task model rejects invalid state."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id=str(uuid.uuid4()),
                description="Test",
                state="INVALID_STATE",  # Invalid state
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        assert "state" in str(exc_info.value)

    def test_rejects_empty_description(self):
        """Test Task model rejects empty description."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id=str(uuid.uuid4()),
                description="",  # Empty description
                state=TaskState.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        assert "description" in str(exc_info.value).lower()

    def test_rejects_whitespace_only_description(self):
        """Test Task model rejects whitespace-only description."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id=str(uuid.uuid4()),
                description="   ",  # Whitespace only
                state=TaskState.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        assert "description" in str(exc_info.value).lower()

    def test_strips_whitespace_from_description(self):
        """Test Task model strips leading/trailing whitespace from description."""
        task = Task(
            id=str(uuid.uuid4()),
            description="  Test task  ",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert task.description == "Test task"

    def test_accepts_long_description(self):
        """Test Task model accepts description up to 2000 characters."""
        long_description = "x" * 2000

        task = Task(
            id=str(uuid.uuid4()),
            description=long_description,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert len(task.description) == 2000

    def test_rejects_too_long_description(self):
        """Test Task model rejects description over 2000 characters."""
        too_long_description = "x" * 2001

        with pytest.raises(ValidationError) as exc_info:
            Task(
                id=str(uuid.uuid4()),
                description=too_long_description,
                state=TaskState.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

        assert "description" in str(exc_info.value).lower()

    def test_accepts_special_characters_in_description(self):
        """Test Task model accepts special characters in description."""
        special_desc = "Review PR #123 & update docs (see: https://example.com)"

        task = Task(
            id=str(uuid.uuid4()),
            description=special_desc,
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        assert task.description == special_desc

    def test_task_serializes_to_dict(self):
        """Test Task model can be serialized to dictionary."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        task = Task(
            id=task_id,
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        task_dict = task.model_dump()

        assert task_dict["id"] == task_id
        assert task_dict["description"] == "Test task"
        assert task_dict["state"] == TaskState.ACTIVE
        assert task_dict["created_at"] == now
        assert task_dict["updated_at"] == now

    def test_task_serializes_to_json(self):
        """Test Task model can be serialized to JSON."""
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        json_str = task.model_dump_json()

        assert isinstance(json_str, str)
        assert "Test task" in json_str
        assert "active" in json_str


class TestTaskEvent:
    """Test TaskEvent model."""

    def test_creates_event_with_valid_data(self):
        """Test TaskEvent accepts valid data."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        event = TaskEvent(
            id=1,
            task_id=task_id,
            event_type="CREATED",
            timestamp=now,
        )

        assert event.id == 1
        assert event.task_id == task_id
        assert event.event_type == "CREATED"
        assert event.timestamp == now
        assert event.metadata is None

    def test_creates_event_with_metadata(self):
        """Test TaskEvent accepts optional metadata."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        metadata = '{"reason": "Not needed anymore"}'

        event = TaskEvent(
            id=1,
            task_id=task_id,
            event_type="CANCELLED",
            timestamp=now,
            metadata=metadata,
        )

        assert event.metadata == metadata

    def test_accepts_standard_event_types(self):
        """Test TaskEvent accepts standard event types."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        event_types = ["CREATED", "COMPLETED", "CANCELLED", "DEFERRED"]

        for event_type in event_types:
            event = TaskEvent(
                id=1,
                task_id=task_id,
                event_type=event_type,
                timestamp=now,
            )
            assert event.event_type == event_type

    def test_event_serializes_to_dict(self):
        """Test TaskEvent can be serialized to dictionary."""
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        event = TaskEvent(
            id=1,
            task_id=task_id,
            event_type="CREATED",
            timestamp=now,
        )

        event_dict = event.model_dump()

        assert event_dict["id"] == 1
        assert event_dict["task_id"] == task_id
        assert event_dict["event_type"] == "CREATED"
        assert event_dict["timestamp"] == now
