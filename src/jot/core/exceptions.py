"""Exception hierarchy for jot application errors."""

import sys

from rich.console import Console

# Create a console instance for error output (always stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)


class JotError(Exception):
    """Base exception for all jot errors.

    All jot-specific exceptions inherit from this class. The exit_code
    attribute determines the process exit code when the exception is raised.

    Attributes:
        exit_code: Process exit code (0=success, 1=user error, 2=system error)
        message: Error message describing what went wrong
    """

    def __init__(self, message: str, exit_code: int = 1) -> None:
        """Initialize JotError.

        Args:
            message: Human-readable error message
            exit_code: Process exit code (default: 1 for user error)
        """
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


class TaskNotFoundError(JotError):
    """Raised when a referenced task doesn't exist.

    This is a user error (exit_code=1) because the user referenced
    a task that doesn't exist, possibly due to a typo or misunderstanding.
    """

    def __init__(self, message: str = "Task not found") -> None:
        """Initialize TaskNotFoundError.

        Args:
            message: Error message describing which task wasn't found
        """
        super().__init__(message, exit_code=1)


class TaskStateError(JotError):
    """Raised when a task state transition is invalid.

    This is a user error (exit_code=1) because the user attempted
    an invalid operation (e.g., completing an already-completed task).
    """

    def __init__(self, message: str) -> None:
        """Initialize TaskStateError.

        Args:
            message: Error message describing the invalid state transition
        """
        super().__init__(message, exit_code=1)


class DatabaseError(JotError):
    """Raised when a database operation fails.

    This is a system error (exit_code=2) because database failures
    indicate a problem with the system, not user input.
    """

    def __init__(self, message: str) -> None:
        """Initialize DatabaseError.

        Args:
            message: Error message describing the database failure
        """
        super().__init__(message, exit_code=2)


class ConfigError(JotError):
    """Raised when configuration is invalid or cannot be loaded.

    This is a user error (exit_code=1) because configuration issues
    are typically due to user misconfiguration or corrupted config files.
    """

    def __init__(self, message: str) -> None:
        """Initialize ConfigError.

        Args:
            message: Error message describing the configuration problem
        """
        super().__init__(message, exit_code=1)


class IPCError(JotError):
    """Raised when an IPC operation fails.

    This is a system error (exit_code=2) because IPC failures indicate
    a problem with inter-process communication, not user input.
    """

    def __init__(self, message: str) -> None:
        """Initialize IPCError.

        Args:
            message: Error message describing the IPC failure
        """
        super().__init__(message, exit_code=2)


def display_error(
    error: JotError,
    console: Console | None = None,
    suggestion: str | None = None,
) -> None:
    """Display an error message with optional recovery suggestion.

    This function formats and displays errors using Rich console,
    ensuring all error output goes to stderr, never stdout.

    Args:
        console: Rich Console instance (defaults to stderr console)
        error: JotError instance to display
        suggestion: Optional recovery suggestion message
    """
    if console is None:
        console = _error_console

    # Format error message with Rich markup
    console.print(f"[red]❌ Error:[/] {error.message}")

    # Add recovery suggestion if provided
    if suggestion:
        console.print(f"[cyan]💡 Suggestion:[/] {suggestion}")
