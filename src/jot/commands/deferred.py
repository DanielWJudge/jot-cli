"""jot deferred command implementation."""

import sys
from datetime import UTC, datetime, timedelta

import typer
from rich.console import Console
from rich.table import Table

from jot.db.exceptions import DatabaseError
from jot.db.repository import TaskRepository

# Create console for success messages (stdout)
_console = Console()
# Create console for error messages (stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


def format_deferred_date(deferred_at: datetime) -> str:
    """Format deferred date in human-readable format.

    Args:
        deferred_at: Deferral timestamp (UTC).

    Returns:
        Human-readable string like "Today", "Yesterday", "2 days ago", "Jan 25, 2026", etc.
    """
    now = datetime.now(UTC)
    elapsed = now - deferred_at

    # Handle negative elapsed time (clock skew or future timestamp)
    if elapsed < timedelta(0):
        return "Today"

    if elapsed < timedelta(days=1):
        return "Today"
    elif elapsed < timedelta(days=2):
        return "Yesterday"
    elif elapsed < timedelta(days=7):
        days = elapsed.days
        return f"{days} days ago"
    else:
        return deferred_at.strftime("%b %d, %Y")


def deferred_command() -> None:
    """List all deferred tasks.

    Displays all deferred tasks with their descriptions, deferral dates,
    and reasons. Tasks are numbered for easy selection with `jot resume`.

    Examples:
        jot deferred              # List all deferred tasks

    Exit Codes:
        0: Success (even if no deferred tasks)
        2: Database error (system error)
    """
    try:
        # Get deferred tasks
        repo = TaskRepository()
        deferred_tasks = repo.get_deferred_tasks()

        if not deferred_tasks:
            # Empty state
            _console.print("No deferred tasks")
            return

        # Display deferred tasks
        table = Table(title="Deferred Tasks", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=3)
        table.add_column("Description", style="cyan")
        table.add_column("Deferred", style="dim")
        table.add_column("Reason", style="yellow")

        for idx, task in enumerate(deferred_tasks, start=1):
            deferred_date = (
                format_deferred_date(task.deferred_at) if task.deferred_at else "Unknown"
            )
            reason = task.defer_reason or "No reason provided"
            table.add_row(
                str(idx),
                task.description,
                deferred_date,
                reason,
            )

        _console.print(table)

    except DatabaseError as e:
        # Handle database errors (system errors, exit code 2)
        _error_console.print(f"[red]❌ Database Error:[/] {e.message}")
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Check database integrity with 'jot doctor' (when implemented)"
        )
        raise typer.Exit(2) from e
