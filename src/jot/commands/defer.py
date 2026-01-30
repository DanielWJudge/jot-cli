"""jot defer command implementation."""

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


def defer_command(
    reason: str | None = typer.Argument(
        None,
        help="Reason for deferring the task. If not provided, you'll be prompted interactively.",
    ),
) -> None:
    """Defer the current active task with a reason.

    Defers the active task by updating its state to DEFERRED,
    recording the deferral timestamp and reason, and logging
    a TASK_DEFERRED event with the reason in metadata.
    Deferred tasks can be resumed later using `jot resume`.
    This clears the active task slot, allowing you to start a new task.

    Examples:
        jot defer "waiting for API access"  # Defer with reason
        jot defer                           # Prompts for reason interactively

    Arguments:
        reason: Reason for deferring the task. If not provided, you'll be prompted interactively.

    Exit Codes:
        0: Task deferred successfully
        1: No active task exists (user error)
        2: Database error (system error)
    """
    try:
        # Get active task
        repo = TaskRepository()
        active_task = repo.get_active_task()

        if active_task is None:
            # No active task - user error
            _error_console.print("[red]❌ Error:[/] No active task to defer")
            _error_console.print(
                '[cyan]💡 Suggestion:[/] Add a task with: jot add "task description"'
            )
            raise typer.Exit(1)

        # Handle interactive prompt if no reason provided
        if reason is None:
            reason = typer.prompt("Why are you deferring this task?")

        # Validate reason (cannot be empty/whitespace)
        if not reason or not reason.strip():
            _error_console.print("[red]❌ Error:[/] Deferral reason cannot be empty")
            raise typer.Exit(1)

        reason = reason.strip()

        # Update task to deferred state
        now = datetime.now(UTC)
        deferred_task = Task(
            id=active_task.id,
            description=active_task.description,
            state=TaskState.DEFERRED,
            created_at=active_task.created_at,
            updated_at=now,
            completed_at=None,  # Clear completed_at (task is deferred, not completed)
            cancelled_at=None,  # Clear cancelled_at (task is deferred, not cancelled)
            cancel_reason=None,  # Clear cancel_reason
            deferred_at=now,  # Set deferral timestamp
            defer_reason=reason,  # Set deferral reason
            deferred_until=active_task.deferred_until,  # Preserve if was already set
        )

        # Create TASK_DEFERRED event with reason in metadata
        metadata = json.dumps({"reason": reason})
        event = TaskEvent(
            id=0,  # Auto-increment in database
            task_id=deferred_task.id,
            event_type="DEFERRED",
            timestamp=now,
            metadata=metadata,  # Store reason as JSON string
        )

        # Persist updated task and event atomically
        repo.update_task_with_event(deferred_task, event)

        # Display success message
        _console.print(
            f"⏸️ Deferred: {deferred_task.description} ({reason})",
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
