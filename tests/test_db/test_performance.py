"""Performance tests for database query requirements (NFR3).

Tests verify that database queries complete within 10ms as required.
"""

import time
import uuid
from datetime import UTC, datetime

import pytest

from jot.core.task import Task, TaskState
from jot.db.repository import TaskRepository


class TestQueryPerformance:
    """Test database query performance requirements."""

    def test_get_task_by_id_completes_under_10ms(self, temp_db):
        """Test get_task_by_id() completes in <10ms (NFR3)."""
        repo = TaskRepository()

        # Create a task to retrieve
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Performance test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Measure query performance
        start_time = time.perf_counter()
        retrieved = repo.get_task_by_id(task_id)
        end_time = time.perf_counter()

        # Calculate duration in milliseconds
        duration_ms = (end_time - start_time) * 1000

        # Verify query completed in under 10ms
        assert duration_ms < 10, f"Query took {duration_ms:.2f}ms, expected <10ms (NFR3)"
        assert retrieved.id == task_id

    def test_get_active_task_completes_under_10ms(self, temp_db):
        """Test get_active_task() completes in <10ms (NFR3)."""
        repo = TaskRepository()

        # Create an active task
        task_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        task = Task(
            id=task_id,
            description="Active performance test task",
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        repo.create_task(task)

        # Measure query performance
        start_time = time.perf_counter()
        active = repo.get_active_task()
        end_time = time.perf_counter()

        # Calculate duration in milliseconds
        duration_ms = (end_time - start_time) * 1000

        # Verify query completed in under 10ms
        assert duration_ms < 10, f"Query took {duration_ms:.2f}ms, expected <10ms (NFR3)"
        assert active is not None
        assert active.id == task_id

    def test_get_active_task_with_many_tasks_under_10ms(self, temp_db):
        """Test get_active_task() remains fast with 1000+ tasks (NFR3)."""
        repo = TaskRepository()

        # Create 1000 completed tasks
        for i in range(1000):
            task = Task(
                id=str(uuid.uuid4()),
                description=f"Completed task {i}",
                state=TaskState.COMPLETED,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            repo.create_task(task)

        # Create one active task
        active_task_id = str(uuid.uuid4())
        active_task = Task(
            id=active_task_id,
            description="Active task among many",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(active_task)

        # Measure query performance with large dataset
        start_time = time.perf_counter()
        active = repo.get_active_task()
        end_time = time.perf_counter()

        # Calculate duration in milliseconds
        duration_ms = (end_time - start_time) * 1000

        # Verify query still completes in under 10ms even with 1000+ tasks
        assert (
            duration_ms < 10
        ), f"Query took {duration_ms:.2f}ms with 1000+ tasks, expected <10ms (NFR3)"
        assert active is not None
        assert active.id == active_task_id

    def test_get_task_by_id_with_many_tasks_under_10ms(self, temp_db):
        """Test get_task_by_id() remains fast with 1000+ tasks (NFR3)."""
        repo = TaskRepository()

        # Create many tasks
        task_ids = []
        for i in range(1000):
            task_id = str(uuid.uuid4())
            task_ids.append(task_id)
            task = Task(
                id=task_id,
                description=f"Task {i}",
                state=TaskState.COMPLETED if i % 2 == 0 else TaskState.CANCELLED,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                completed_at=(datetime.now(UTC) if i % 2 == 0 else None),
            )
            repo.create_task(task)

        # Pick a random task ID to retrieve
        target_id = task_ids[500]

        # Measure query performance with large dataset
        start_time = time.perf_counter()
        retrieved = repo.get_task_by_id(target_id)
        end_time = time.perf_counter()

        # Calculate duration in milliseconds
        duration_ms = (end_time - start_time) * 1000

        # Verify query completes in under 10ms even with 1000+ tasks
        assert (
            duration_ms < 10
        ), f"Query took {duration_ms:.2f}ms with 1000+ tasks, expected <10ms (NFR3)"
        assert retrieved.id == target_id

    def test_queries_use_indexes_efficiently(self, temp_db):
        """Test queries benefit from database indexes (performance check)."""
        repo = TaskRepository()

        # Create diverse dataset with different states
        for i in range(500):
            for state in [
                TaskState.ACTIVE,
                TaskState.COMPLETED,
                TaskState.CANCELLED,
                TaskState.DEFERRED,
            ]:
                task = Task(
                    id=str(uuid.uuid4()),
                    description=f"Task {i} {state.value}",
                    state=state,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                repo.create_task(task)

        # Query for active task (should use state index)
        start_time = time.perf_counter()
        active = repo.get_active_task()
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        # With 2000 tasks and proper indexing, query should still be <10ms
        assert (
            duration_ms < 10
        ), f"Indexed query took {duration_ms:.2f}ms with 2000 tasks, expected <10ms (NFR3)"
        assert active is not None
        assert active.state == TaskState.ACTIVE

    @pytest.mark.parametrize("num_runs", [10])
    def test_query_performance_consistency(self, temp_db, num_runs):
        """Test query performance is consistently under 10ms across multiple runs."""
        repo = TaskRepository()

        # Create test data
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            description="Consistency test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Run query multiple times and measure each
        durations = []
        for _ in range(num_runs):
            start_time = time.perf_counter()
            repo.get_task_by_id(task_id)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            durations.append(duration_ms)

        # Verify all queries completed in under 10ms
        max_duration = max(durations)
        avg_duration = sum(durations) / len(durations)

        assert (
            max_duration < 10
        ), f"Max query time {max_duration:.2f}ms exceeded 10ms threshold (NFR3)"
        assert (
            avg_duration < 5
        ), f"Average query time {avg_duration:.2f}ms should be well under 10ms"
