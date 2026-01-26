"""jot CLI entry point."""

import typer

app = typer.Typer(
    name="jot",
    help="A terminal-based task execution tool for focused work.",
)


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
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
