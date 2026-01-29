"""Repository classes for task data persistence.

This module provides the data access layer for tasks and task events,
implementing the repository pattern to convert between SQLite rows and
Pydantic domain models.
"""

import sqlite3
from datetime import datetime

from jot.core.exceptions import TaskNotFoundError
from jot.core.task import Task, TaskEvent, TaskState
from jot.db.connection import get_connection
from jot.db.exceptions import DatabaseError


class TaskRepository:
    """Repository for task persistence operations.

    Provides CRUD operations for tasks, converting between SQLite rows
    and Task domain models. All operations are atomic and use transactions
    where appropriate.
    """

    def create_task(self, task: Task) -> None:
        """Create a new task with a CREATED event atomically.

        This method creates both the task and its initial CREATED event
        in a single transaction to ensure data consistency.

        Args:
            task: Task model to create

        Raises:
            DatabaseError: If task creation fails
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Insert task
            cursor.execute(
                """
                INSERT INTO tasks (
                    id, description, state, created_at, updated_at,
                    completed_at, cancelled_at, cancel_reason,
                    deferred_at, defer_reason, deferred_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.description,
                    task.state.value,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.cancelled_at.isoformat() if task.cancelled_at else None,
                    task.cancel_reason,
                    task.deferred_at.isoformat() if task.deferred_at else None,
                    task.defer_reason,
                    task.deferred_until.isoformat() if task.deferred_until else None,
                ),
            )

            # Create CREATED event
            cursor.execute(
                """
                INSERT INTO task_events (task_id, event_type, timestamp)
                VALUES (?, ?, ?)
                """,
                (task.id, "CREATED", task.created_at.isoformat()),
            )

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to create task: {e}") from e
        finally:
            conn.close()

    def get_task_by_id(self, task_id: str) -> Task:
        """Get task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task domain model

        Raises:
            TaskNotFoundError: If task doesn't exist
            DatabaseError: If query fails
        """
        conn = get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            )

            row = cursor.fetchone()
            if row is None:
                raise TaskNotFoundError(f"Task not found: {task_id}")

            return self._row_to_task(row)

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get task: {e}") from e
        finally:
            conn.close()

    def get_active_task(self) -> Task | None:
        """Get the current active task.

        Returns:
            Active task, or None if no active task exists

        Raises:
            DatabaseError: If query fails
        """
        conn = get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM tasks WHERE state = ? LIMIT 1",
                (TaskState.ACTIVE.value,),
            )

            row = cursor.fetchone()
            if row is None:
                return None

            return self._row_to_task(row)

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get active task: {e}") from e
        finally:
            conn.close()

    def get_deferred_tasks(self) -> list[Task]:
        """Get all deferred tasks.

        Returns:
            List of deferred tasks, ordered by deferred_at timestamp (oldest first).

        Raises:
            DatabaseError: If query fails
        """
        conn = get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM tasks WHERE state = ? ORDER BY deferred_at ASC",
                (TaskState.DEFERRED.value,),
            )

            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get deferred tasks: {e}") from e
        finally:
            conn.close()

    def update_task(self, task: Task) -> None:
        """Update an existing task.

        Args:
            task: Task model with updated values

        Raises:
            TaskNotFoundError: If task doesn't exist
            DatabaseError: If update fails
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE tasks
                SET description = ?,
                    state = ?,
                    updated_at = ?,
                    completed_at = ?,
                    cancelled_at = ?,
                    cancel_reason = ?,
                    deferred_at = ?,
                    defer_reason = ?,
                    deferred_until = ?
                WHERE id = ?
                """,
                (
                    task.description,
                    task.state.value,
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.cancelled_at.isoformat() if task.cancelled_at else None,
                    task.cancel_reason,
                    task.deferred_at.isoformat() if task.deferred_at else None,
                    task.defer_reason,
                    task.deferred_until.isoformat() if task.deferred_until else None,
                    task.id,
                ),
            )

            if cursor.rowcount == 0:
                raise TaskNotFoundError(f"Task not found: {task.id}")

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to update task: {e}") from e
        finally:
            conn.close()

    def update_task_with_event(self, task: Task, event: TaskEvent) -> None:
        """Update task and create event atomically in a single transaction.

        This ensures data consistency by committing both operations together.
        If either operation fails, both are rolled back.

        Args:
            task: Task model with updated values
            event: Event to log for this task update

        Raises:
            TaskNotFoundError: If task doesn't exist
            DatabaseError: If update or event creation fails
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()

            # Update task
            cursor.execute(
                """
                UPDATE tasks
                SET description = ?,
                    state = ?,
                    updated_at = ?,
                    completed_at = ?,
                    cancelled_at = ?,
                    cancel_reason = ?,
                    deferred_at = ?,
                    defer_reason = ?,
                    deferred_until = ?
                WHERE id = ?
                """,
                (
                    task.description,
                    task.state.value,
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    task.cancelled_at.isoformat() if task.cancelled_at else None,
                    task.cancel_reason,
                    task.deferred_at.isoformat() if task.deferred_at else None,
                    task.defer_reason,
                    task.deferred_until.isoformat() if task.deferred_until else None,
                    task.id,
                ),
            )

            if cursor.rowcount == 0:
                raise TaskNotFoundError(f"Task not found: {task.id}")

            # Create event in same transaction
            cursor.execute(
                """
                INSERT INTO task_events (task_id, event_type, timestamp, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.task_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    event.metadata,
                ),
            )

            # Commit both operations together
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to update task with event: {e}") from e
        finally:
            conn.close()

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert SQLite row to Task model.

        Args:
            row: SQLite row from tasks table

        Returns:
            Task domain model
        """
        # Handle optional fields with try/except for backward compatibility
        # (columns might not exist in older database versions)
        try:
            cancel_reason = row["cancel_reason"]
        except (KeyError, IndexError):
            cancel_reason = None

        try:
            deferred_at = datetime.fromisoformat(row["deferred_at"]) if row["deferred_at"] else None
        except (KeyError, IndexError):
            deferred_at = None

        try:
            defer_reason = row["defer_reason"]
        except (KeyError, IndexError):
            defer_reason = None

        try:
            deferred_until = (
                datetime.fromisoformat(row["deferred_until"]) if row["deferred_until"] else None
            )
        except (KeyError, IndexError):
            deferred_until = None

        return Task(
            id=row["id"],
            description=row["description"],
            state=TaskState(row["state"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
            ),
            cancelled_at=(
                datetime.fromisoformat(row["cancelled_at"]) if row["cancelled_at"] else None
            ),
            cancel_reason=cancel_reason,
            deferred_at=deferred_at,
            defer_reason=defer_reason,
            deferred_until=deferred_until,
        )


class EventRepository:
    """Repository for task event persistence operations.

    Provides operations for creating and retrieving task events,
    which form the audit trail for task state changes.
    """

    def create_event(self, event: TaskEvent) -> None:
        """Create a new task event.

        Args:
            event: TaskEvent model to create

        Raises:
            DatabaseError: If event creation fails
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO task_events (task_id, event_type, timestamp, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.task_id,
                    event.event_type,
                    event.timestamp.isoformat(),
                    event.metadata,
                ),
            )

            conn.commit()

        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to create event: {e}") from e
        finally:
            conn.close()

    def get_events_for_task(self, task_id: str) -> list[TaskEvent]:
        """Get all events for a task.

        Args:
            task_id: Task ID to get events for

        Returns:
            List of task events, ordered by timestamp

        Raises:
            DatabaseError: If query fails
        """
        conn = get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM task_events WHERE task_id = ? ORDER BY timestamp",
                (task_id,),
            )

            rows = cursor.fetchall()
            return [self._row_to_event(row) for row in rows]

        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get events: {e}") from e
        finally:
            conn.close()

    def _row_to_event(self, row: sqlite3.Row) -> TaskEvent:
        """Convert SQLite row to TaskEvent model.

        Args:
            row: SQLite row from task_events table

        Returns:
            TaskEvent domain model
        """
        return TaskEvent(
            id=row["id"],
            task_id=row["task_id"],
            event_type=row["event_type"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=row["metadata"],
        )
