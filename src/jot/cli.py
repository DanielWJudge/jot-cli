"""jot CLI entry point."""

import typer

app = typer.Typer(
    name="jot",
    help="A terminal-based task execution tool for focused work.",
)


@app.command()
def help():
    """Show help message."""
    typer.echo("jot - A terminal-based task execution tool")
    typer.echo("Run 'jot --help' for available commands")


if __name__ == "__main__":
    app()
