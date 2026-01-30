"""jot done command implementation."""

import contextlib
import sys
from datetime import UTC, datetime

import typer
from rich.console import Console

from jot.core.exceptions import TaskNotFoundError, display_error
from jot.core.task import Task, TaskEvent, TaskState
from jot.db.exceptions import DatabaseError
from jot.db.repository import EventRepository, TaskRepository
from jot.ipc import notify_monitor
from jot.ipc.events import IPCEvent

# Create console for success messages (stdout)
_console = Console()
# Create console for error messages (stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


def done_command() -> None:
    """Mark the current active task as completed.

    Completes the active task by updating its state to COMPLETED,
    recording the completion timestamp, and logging a TASK_COMPLETED event.
    This clears the active task slot, allowing you to start a new task.

    Examples:
        jot done  # Completes the current active task

    Exit Codes:
        0: Task completed successfully
        1: No active task exists (user error)
        2: Database error (system error)
    """
    try:
        # Get active task
        repo = TaskRepository()
        active_task = repo.get_active_task()

        if active_task is None:
            # No active task - user error
            _error_console.print("[red]❌ Error:[/] No active task to complete")
            _error_console.print(
                '[cyan]💡 Suggestion:[/] Start a new task with: jot add "task description"'
            )
            raise typer.Exit(1)

        # Update task to completed state
        now = datetime.now(UTC)
        completed_task = Task(
            id=active_task.id,
            description=active_task.description,
            state=TaskState.COMPLETED,
            created_at=active_task.created_at,
            updated_at=now,
            completed_at=now,  # Set completion timestamp
        )

        # Persist updated task
        repo.update_task(completed_task)

        # Log TASK_COMPLETED event
        event_repo = EventRepository()
        event = TaskEvent(
            id=0,  # Auto-increment in database
            task_id=completed_task.id,
            event_type="COMPLETED",
            timestamp=now,
            metadata=None,
        )
        event_repo.create_event(event)

        # Notify monitor of task completion (fire-and-forget)
        # Only suppress expected IPC socket errors, let programming errors fail
        with contextlib.suppress(OSError, ConnectionError, TimeoutError):
            notify_monitor(IPCEvent.TASK_COMPLETED, completed_task.id)

        # Display success message
        _console.print(f"✅ Completed: {completed_task.description}", style="green")

    except DatabaseError as e:
        # Handle database errors (system errors, exit code 2)
        _error_console.print(f"[red]❌ Database Error:[/] {e.message}")
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Check database integrity with 'jot doctor' (when implemented)"
        )
        raise typer.Exit(2) from e
    except TaskNotFoundError as e:
        # This shouldn't happen with active task, but handle it
        display_error(e, _error_console)
        raise typer.Exit(e.exit_code) from e
