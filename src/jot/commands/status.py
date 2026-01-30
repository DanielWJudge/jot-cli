"""jot status command implementation."""

import sys
from datetime import UTC, datetime, timedelta

import typer
from rich.console import Console

from jot.db.exceptions import DatabaseError
from jot.db.repository import TaskRepository

# Create console for success messages (stdout)
_console = Console()
# Create console for error messages (stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


def format_time_elapsed(created_at: datetime) -> str:
    """Format time elapsed since creation in human-readable format.

    Args:
        created_at: Task creation timestamp (UTC).

    Returns:
        Human-readable string like "just now", "5 minutes ago", "2 hours ago", etc.
    """
    now = datetime.now(UTC)
    elapsed = now - created_at

    # Handle negative elapsed time (clock skew or future timestamp)
    if elapsed < timedelta(0):
        return "just now"

    if elapsed < timedelta(minutes=1):
        return "just now"
    elif elapsed < timedelta(hours=1):
        minutes = int(elapsed.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif elapsed < timedelta(days=1):
        hours = int(elapsed.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(elapsed.total_seconds() / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def status_command(
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Quiet mode: exit code 0 if active task exists, 1 if not. No output.",
    ),
) -> None:
    """Display the current active task.

    Shows the active task with emoji, description, and time elapsed
    since creation. Useful for quickly checking what you should be
    working on.

    Examples:
        jot status              # Display active task
        jot status --quiet      # Exit code only (for scripting)

    Options:
        --quiet, -q: Quiet mode: exit code 0 if active task exists, 1 if not. No output.

    Exit Codes:
        0: Active task exists (or quiet mode with task)
        1: No active task exists (user error)
        2: Database error (system error)
    """
    try:
        # Get active task
        repo = TaskRepository()
        active_task = repo.get_active_task()

        if active_task is None:
            # No active task
            if quiet:
                # Quiet mode: exit code only, no output
                raise typer.Exit(1)

            # Normal mode: show helpful message
            _error_console.print("[red]No active task[/]")
            _error_console.print(
                '[cyan]💡 Suggestion:[/] Start one with: jot add "task description"'
            )
            raise typer.Exit(1)

        # Active task exists
        if quiet:
            # Quiet mode: exit code only, no output
            raise typer.Exit(0)

        # Normal mode: display task
        time_elapsed = format_time_elapsed(active_task.created_at)
        _console.print(f"🎯 [cyan]{active_task.description}[/]")
        _console.print(f"[dim]started {time_elapsed}[/]")

    except DatabaseError as e:
        # Handle database errors (system errors, exit code 2)
        _error_console.print(f"[red]❌ Database Error:[/] {e.message}")
        _error_console.print(
            "[cyan]💡 Suggestion:[/] Check database integrity with 'jot doctor' (when implemented)"
        )
        raise typer.Exit(2) from e
