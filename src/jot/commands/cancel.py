"""jot cancel command implementation."""

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


def cancel_command(
    reason: str | None = typer.Argument(None, help="Reason for cancelling the task"),
) -> None:
    """Cancel the current active task with a reason.

    Cancels the active task by updating its state to CANCELLED,
    recording the cancellation timestamp and reason, and logging
    a TASK_CANCELLED event with the reason in metadata.

    Examples:
        jot cancel "out of scope"  # Cancel with reason
        jot cancel  # Prompts for reason interactively

    Exit Codes:
        0: Task cancelled successfully
        1: No active task exists (user error)
        2: Database error (system error)
    """
    try:
        # Get active task
        repo = TaskRepository()
        active_task = repo.get_active_task()

        if active_task is None:
            # No active task - user error
            _error_console.print("[red]❌ Error:[/] No active task to cancel")
            _error_console.print(
                '[cyan]💡 Suggestion:[/] Add a task with: jot add "task description"'
            )
            raise typer.Exit(1)

        # Handle interactive prompt if no reason provided
        if reason is None:
            reason = typer.prompt("Why are you cancelling this task?")

        # Validate reason (cannot be empty/whitespace)
        if not reason or not reason.strip():
            _error_console.print("[red]❌ Error:[/] Cancellation reason cannot be empty")
            raise typer.Exit(1)

        reason = reason.strip()

        # Update task to cancelled state
        now = datetime.now(UTC)
        cancelled_task = Task(
            id=active_task.id,
            description=active_task.description,
            state=TaskState.CANCELLED,
            created_at=active_task.created_at,
            updated_at=now,
            completed_at=None,  # Clear completed_at (task is cancelled, not completed)
            cancelled_at=now,  # Set cancellation timestamp
            cancel_reason=reason,  # Set cancellation reason
            deferred_until=None,  # Clear deferred_until (task is cancelled, not deferred)
        )

        # Create TASK_CANCELLED event with reason in metadata
        metadata = json.dumps({"reason": reason})
        event = TaskEvent(
            id=0,  # Auto-increment in database
            task_id=cancelled_task.id,
            event_type="CANCELLED",
            timestamp=now,
            metadata=metadata,  # Store reason as JSON string
        )

        # Persist updated task and event atomically
        repo.update_task_with_event(cancelled_task, event)

        # Display success message
        _console.print(
            f"❌ Cancelled: {cancelled_task.description} ({reason})",
            style="green",
        )

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
