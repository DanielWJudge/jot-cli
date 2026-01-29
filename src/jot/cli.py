"""jot CLI entry point."""

import typer
from rich.console import Console

from jot import __version__
from jot.commands.add import add_command
from jot.commands.cancel import cancel_command
from jot.commands.defer import defer_command
from jot.commands.deferred import deferred_command
from jot.commands.done import done_command
from jot.commands.resume import resume_command
from jot.commands.status import status_command

app = typer.Typer(
    name="jot",
    help="Personal task management tool - focus on one task at a time.",
    rich_markup_mode="rich",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


# Register commands
app.command(name="add")(add_command)
app.command(name="cancel")(cancel_command)
app.command(name="defer")(defer_command)
app.command(name="deferred")(deferred_command)
app.command(name="done")(done_command)
app.command(name="resume")(resume_command)
app.command(name="status")(status_command)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
) -> None:
    """Main callback - handles version flag and no-command case."""
    if version:
        console = Console()
        console.print(f"jot version {__version__}")
        raise typer.Exit(0)

    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        console = Console()
        console.print(ctx.get_help())
        raise typer.Exit(0)


def main() -> None:
    """Entry point for the CLI application.

    Typer automatically handles invalid commands with suggestions when
    rich_markup_mode="rich" is enabled. Commands handle their own errors
    and exit with appropriate codes.
    """
    app()


if __name__ == "__main__":
    main()
