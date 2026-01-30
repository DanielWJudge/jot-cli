"""jot add command implementation."""

import sys
import uuid
from datetime import UTC, datetime

import typer
from rich.console import Console

from jot.core.exceptions import JotError, display_error
from jot.core.task import Task, TaskState
from jot.db.exceptions import DatabaseError
from jot.db.repository import TaskRepository

# Create console for success messages (stdout)
_console = Console()
# Create console for error messages (stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


def add_command(
    description: str | None = typer.Argument(
        None,
        help="Task description. If not provided, you'll be prompted interactively.",
    ),
) -> None:
    """Add a new task to your active task list.

    Creates a new task and sets it as the active task. If an active task already
    exists, you'll be prompted to handle the conflict first (complete, cancel, or defer it).

    Examples:
        jot add "Review PR for auth feature"    # Add task with description
        jot add                                 # Interactive prompt for description

    Arguments:
        description: Task description. If not provided, you'll be prompted interactively.

    Exit Codes:
        0: Task added successfully
        1: User error (invalid input, conflict not resolved)
        2: System error (database failure)
    """
    try:
        # Handle interactive prompt if no description provided
        if description is None:
            description = typer.prompt("What's your task?")

        # Validate description (cannot be empty/whitespace)
        if not description or not description.strip():
            _error_console.print("[red]❌ Error:[/] Description cannot be empty")
            raise typer.Exit(1)

        # Check for existing active task
        repo = TaskRepository()
        existing_active = repo.get_active_task()

        if existing_active is not None:
            # Show warning and prompt for action
            _console.print(
                f"⚠️  You already have an active task: {existing_active.description}",
                style="yellow",
            )

            action = typer.prompt(
                "Complete, cancel, or defer it first? [d]one/[c]ancel/[D]efer/[f]orce",
                default="D",
            )

            if action.lower() == "f":
                # Force: Cancel the existing active task and create new one
                # This is a workaround until proper task state transitions are implemented
                _console.print(
                    "⚠️  Forcing new task (existing task will remain active until proper handling is implemented)",
                    style="yellow",
                )
                # Note: This will fail with database constraint violation
                # TODO: Implement proper active task replacement in future stories
                # For now, we show the warning and let the database error be caught below
            else:
                # Other options: show message (will be implemented in future stories)
                _console.print(
                    "Please use 'jot done', 'jot cancel', or 'jot defer' first.",
                    style="yellow",
                )
                raise typer.Exit(1)

        # Create new task
        now = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            description=description.strip(),
            state=TaskState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        # Persist task (creates task + CREATED event atomically)
        repo.create_task(task)

        # Display success message
        _console.print(f"🎯 Added: {task.description}", style="green")
    except DatabaseError as e:
        # Handle database errors (system errors, exit code 2)
        _error_console.print(f"[red]❌ Database Error:[/] {e.message}")
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Check database integrity with 'jot doctor' (when implemented)"
        )
        raise typer.Exit(2) from e
    except JotError as e:
        # Handle application errors (user errors, exit code 1)
        display_error(e, _error_console)
        raise typer.Exit(e.exit_code) from e
