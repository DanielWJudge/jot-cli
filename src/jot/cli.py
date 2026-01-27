"""jot CLI entry point."""

import sys
from collections.abc import Callable

import typer
from rich.console import Console

from jot.commands.add import add_command
from jot.core.exceptions import JotError, display_error

# Create console instance for error output (always stderr)
_error_console = Console(file=sys.stderr, force_terminal=True)

app = typer.Typer(
    name="jot",
    help="A terminal-based task execution tool for focused work.",
)


def handle_jot_errors[T](func: Callable[[], T]) -> Callable[[], T]:
    """Decorator to handle JotError exceptions in command handlers.

    This decorator catches JotError exceptions, displays them using Rich console
    to stderr, and raises SystemExit with the appropriate exit code.

    Example:
        @app.command()
        @handle_jot_errors
        def my_command() -> None:
            # Command implementation that may raise JotError
            raise TaskNotFoundError("Task not found")
    """

    def wrapper() -> T:
        try:
            return func()
        except JotError as e:
            display_error(e, _error_console)
            raise SystemExit(e.exit_code) from None

    return wrapper


# Register add command
app.command(name="add")(add_command)


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context) -> None:
    """
    Jot - A terminal-based task execution tool.

    Run 'jot --help' to see available commands.
    """
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


def main() -> None:
    """Entry point for the CLI application.

    This function wraps the Typer app execution to catch any JotError
    exceptions that might escape command handlers and handle them properly.
    """
    try:
        app()
    except JotError as e:
        display_error(e, _error_console)
        raise SystemExit(e.exit_code) from None


if __name__ == "__main__":
    main()
