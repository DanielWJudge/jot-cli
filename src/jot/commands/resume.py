"""jot resume command implementation."""

import json
import sys
from datetime import UTC, datetime

import typer
from rich.console import Console

from jot.core.exceptions import TaskNotFoundError, display_error
from jot.core.task import Task, TaskEvent, TaskState
from jot.db.exceptions import DatabaseError
from jot.db.repository import TaskRepository

# Create console for success messages (stdout)
_console = Console()
# Create console for error messages (stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


def parse_task_identifier(task_id: str, repo: TaskRepository) -> str:
    """Parse task identifier (number or UUID).

    Args:
        task_id: Task identifier (number from deferred list or UUID).
        repo: TaskRepository instance for querying deferred tasks.

    Returns:
        Task UUID string.

    Raises:
        TaskNotFoundError: If task identifier is invalid.
    """
    # Try parsing as number (from deferred list)
    try:
        task_num = int(task_id)
        if task_num < 1:
            raise TaskNotFoundError(f"Invalid task number: {task_num}")

        # Get deferred tasks and select by number
        deferred_tasks = repo.get_deferred_tasks()

        if task_num > len(deferred_tasks):
            raise TaskNotFoundError(
                f"Task number {task_num} not found (only {len(deferred_tasks)} deferred tasks)"
            )

        return deferred_tasks[task_num - 1].id  # Convert to 0-based index

    except ValueError:
        # Not a number, assume it's a UUID
        return task_id


def resume_command(
    task_id: str = typer.Argument(..., help="Task ID or number from deferred list"),
) -> None:
    """Resume a deferred task as the active task.

    Resumes a deferred task by changing its state from DEFERRED to ACTIVE.
    If an active task already exists, prompts user to handle the conflict.

    Examples:
        jot resume 1              # Resume first deferred task (by number)
        jot resume <uuid>          # Resume task by UUID

    Exit Codes:
        0: Task resumed successfully
        1: Task not found, invalid state, or user error
        2: Database error (system error)
    """
    try:
        # Create single repository instance for all operations
        repo = TaskRepository()

        # Parse task identifier
        task_uuid = parse_task_identifier(task_id, repo)

        # Get task
        task = repo.get_task_by_id(task_uuid)

        # Validate task is deferred
        if task.state != TaskState.DEFERRED:
            _error_console.print(
                f"[red]❌ Error:[/] Task is not deferred (current state: {task.state.value})"
            )
            _error_console.print(
                "[cyan]💡 Suggestion:[/] Only deferred tasks can be resumed. Use 'jot deferred' to see deferred tasks."
            )
            raise typer.Exit(1)

        # Check for active task conflict
        active_task = repo.get_active_task()
        if active_task is not None:
            # Conflict - prompt user
            _error_console.print(
                f"[yellow]⚠️ Warning:[/] You already have an active task: {active_task.description}"
            )
            choice_raw = typer.prompt(
                "Complete, cancel, or defer it first? [d]one/[c]ancel/[D]efer/[f]orce",
                default="d",
            )
            choice = choice_raw.lower()

            if choice == "f":
                # Force: defer current active task, then resume deferred task
                now = datetime.now(UTC)
                defer_reason = "Replaced by resumed task"
                deferred_active = Task(
                    id=active_task.id,
                    description=active_task.description,
                    state=TaskState.DEFERRED,
                    created_at=active_task.created_at,
                    updated_at=now,
                    completed_at=None,
                    cancelled_at=None,
                    cancel_reason=None,
                    deferred_at=now,
                    defer_reason=defer_reason,
                    deferred_until=None,
                )
                defer_event = TaskEvent(
                    id=0,
                    task_id=active_task.id,
                    event_type="DEFERRED",
                    timestamp=now,
                    metadata=json.dumps({"reason": defer_reason}),
                )
                repo.update_task_with_event(deferred_active, defer_event)
            elif choice == "d" and choice_raw != "D":
                # Done: complete current task first (lowercase 'd')
                now = datetime.now(UTC)
                completed_active = Task(
                    id=active_task.id,
                    description=active_task.description,
                    state=TaskState.COMPLETED,
                    created_at=active_task.created_at,
                    updated_at=now,
                    completed_at=now,
                    cancelled_at=None,
                    cancel_reason=None,
                    deferred_at=None,
                    defer_reason=None,
                    deferred_until=None,
                )
                complete_event = TaskEvent(
                    id=0,
                    task_id=active_task.id,
                    event_type="COMPLETED",
                    timestamp=now,
                    metadata=None,
                )
                repo.update_task_with_event(completed_active, complete_event)
            elif choice == "c":
                # Cancel: cancel current task first
                cancel_reason = "Replaced by resumed task"
                now = datetime.now(UTC)
                cancelled_active = Task(
                    id=active_task.id,
                    description=active_task.description,
                    state=TaskState.CANCELLED,
                    created_at=active_task.created_at,
                    updated_at=now,
                    completed_at=None,
                    cancelled_at=now,
                    cancel_reason=cancel_reason,
                    deferred_at=None,
                    defer_reason=None,
                    deferred_until=None,
                )
                cancel_event = TaskEvent(
                    id=0,
                    task_id=active_task.id,
                    event_type="CANCELLED",
                    timestamp=now,
                    metadata=json.dumps({"reason": cancel_reason}),
                )
                repo.update_task_with_event(cancelled_active, cancel_event)
            elif choice == "defer" or choice_raw == "D":
                # Defer: defer current task first (uppercase 'D' or 'defer')
                defer_reason = "Replaced by resumed task"
                now = datetime.now(UTC)
                deferred_active = Task(
                    id=active_task.id,
                    description=active_task.description,
                    state=TaskState.DEFERRED,
                    created_at=active_task.created_at,
                    updated_at=now,
                    completed_at=None,
                    cancelled_at=None,
                    cancel_reason=None,
                    deferred_at=now,
                    defer_reason=defer_reason,
                    deferred_until=None,
                )
                defer_event = TaskEvent(
                    id=0,
                    task_id=active_task.id,
                    event_type="DEFERRED",
                    timestamp=now,
                    metadata=json.dumps({"reason": defer_reason}),
                )
                repo.update_task_with_event(deferred_active, defer_event)
            else:
                _error_console.print("[red]❌ Error:[/] Invalid choice")
                raise typer.Exit(1)

        # Resume task
        now = datetime.now(UTC)
        resumed_task = Task(
            id=task.id,
            description=task.description,
            state=TaskState.ACTIVE,
            created_at=task.created_at,
            updated_at=now,
            completed_at=task.completed_at,  # Preserve if was completed before deferral
            cancelled_at=None,  # Clear cancelled fields
            cancel_reason=None,
            deferred_at=None,  # Clear deferred fields
            defer_reason=None,
            deferred_until=None,
        )

        # Create TASK_RESUMED event
        event = TaskEvent(
            id=0,  # Auto-increment in database
            task_id=resumed_task.id,
            event_type="RESUMED",
            timestamp=now,
            metadata=None,
        )

        # Update task and create event atomically
        repo.update_task_with_event(resumed_task, event)

        # Display success message
        _console.print(f"🎯 Resumed: {resumed_task.description}", style="green")

    except DatabaseError as e:
        # Handle database errors (system errors, exit code 2)
        _error_console.print(f"[red]❌ Database Error:[/] {e.message}")
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Check database integrity with 'jot doctor' (when implemented)"
        )
        raise typer.Exit(2) from e
    except TaskNotFoundError as e:
        display_error(e, _error_console)
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Use 'jot deferred' to see available deferred tasks."
        )
        raise typer.Exit(e.exit_code) from e
