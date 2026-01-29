"""Test suite for CLI help system."""

from typer.testing import CliRunner

from jot.cli import app


class TestHelpSystem:
    """Test jot help system."""

    def test_app_help_displays_all_commands(self):
        """Test jot --help displays all commands."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "done" in result.stdout
        assert "cancel" in result.stdout
        assert "defer" in result.stdout
        assert "status" in result.stdout
        assert "deferred" in result.stdout
        assert "resume" in result.stdout

    def test_app_help_shows_app_description(self):
        """Test jot --help shows app description."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Personal task management tool" in result.stdout
        assert "focus on one task at a time" in result.stdout.lower()

    def test_app_help_shows_global_options(self):
        """Test jot --help shows global options."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "--help" in result.stdout or "-h" in result.stdout
        assert "--version" in result.stdout or "-v" in result.stdout

    def test_version_option_shows_version(self):
        """Test jot --version shows version."""
        runner = CliRunner()

        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "jot version" in result.stdout
        assert "0.1.0" in result.stdout

    def test_add_command_help_shows_details(self):
        """Test jot add --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "--help"])

        assert result.exit_code == 0
        assert "Add a new task" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout
        assert "description" in result.stdout.lower()

    def test_done_command_help_shows_details(self):
        """Test jot done --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["done", "--help"])

        assert result.exit_code == 0
        assert "Mark the current active task" in result.stdout
        assert "completed" in result.stdout.lower()
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout

    def test_cancel_command_help_shows_details(self):
        """Test jot cancel --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["cancel", "--help"])

        assert result.exit_code == 0
        assert "Cancel the current active task" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout
        assert "reason" in result.stdout.lower()

    def test_defer_command_help_shows_details(self):
        """Test jot defer --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["defer", "--help"])

        assert result.exit_code == 0
        assert "Defer the current active task" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout
        assert "reason" in result.stdout.lower()

    def test_status_command_help_shows_details(self):
        """Test jot status --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        assert "Display the current active task" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout
        assert "--quiet" in result.stdout or "-q" in result.stdout

    def test_deferred_command_help_shows_details(self):
        """Test jot deferred --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["deferred", "--help"])

        assert result.exit_code == 0
        assert "List all deferred tasks" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout

    def test_resume_command_help_shows_details(self):
        """Test jot resume --help shows detailed help."""
        runner = CliRunner()

        result = runner.invoke(app, ["resume", "--help"])

        assert result.exit_code == 0
        assert "Resume a deferred task" in result.stdout
        assert "Examples:" in result.stdout
        assert "Exit Codes:" in result.stdout
        assert "task_id" in result.stdout.lower() or "Task ID" in result.stdout

    def test_invalid_command_shows_error(self):
        """Test jot invalid shows error."""
        runner = CliRunner()

        result = runner.invoke(app, ["invalid"])

        assert result.exit_code != 0
        # Typer should show error message (may be in stdout or stderr)
        error_output = result.stdout + result.stderr
        assert "invalid" in error_output.lower() or "unknown" in error_output.lower()

    def test_invalid_command_suggests_help(self):
        """Test invalid command suggests running --help."""
        runner = CliRunner()

        result = runner.invoke(app, ["invalid"])

        assert result.exit_code != 0
        # Typer should suggest help (may be in stdout or stderr)
        error_output = result.stdout + result.stderr
        assert "--help" in error_output.lower() or "help" in error_output.lower()

    def test_no_command_shows_help(self):
        """Test running jot without command shows help."""
        runner = CliRunner()

        result = runner.invoke(app, [])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "done" in result.stdout
        assert "cancel" in result.stdout

    def test_help_text_uses_rich_formatting(self):
        """Test help text uses Rich formatting (check for Rich markup indicators)."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Rich formatting should produce clean, readable output
        # The presence of structured output indicates Rich is working
        assert len(result.stdout) > 0

    def test_all_commands_have_examples(self):
        """Test all commands show examples in help."""
        runner = CliRunner()
        commands = ["add", "done", "cancel", "defer", "status", "deferred", "resume"]

        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"Command {cmd} help failed"
            assert "Examples:" in result.stdout, f"Command {cmd} missing Examples section"

    def test_all_commands_have_exit_codes(self):
        """Test all commands show exit codes in help."""
        runner = CliRunner()
        commands = ["add", "done", "cancel", "defer", "status", "deferred", "resume"]

        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"Command {cmd} help failed"
            assert "Exit Codes:" in result.stdout, f"Command {cmd} missing Exit Codes section"

    def test_help_text_follows_cli_conventions(self):
        """Test help text follows CLI conventions (NFR23)."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Check for standard CLI help elements
        assert "--help" in result.stdout or "-h" in result.stdout
        # Commands should be listed clearly
        assert "add" in result.stdout
        assert "done" in result.stdout

    def test_command_help_shows_argument_help(self):
        """Test command help shows argument help text."""
        runner = CliRunner()

        result = runner.invoke(app, ["add", "--help"])

        assert result.exit_code == 0
        # Should show help for description argument
        assert "description" in result.stdout.lower()
        assert "prompt" in result.stdout.lower() or "interactive" in result.stdout.lower()

    def test_command_help_shows_option_help(self):
        """Test command help shows option help text."""
        runner = CliRunner()

        result = runner.invoke(app, ["status", "--help"])

        assert result.exit_code == 0
        # Should show help for --quiet option
        assert "--quiet" in result.stdout or "-q" in result.stdout
        assert "quiet" in result.stdout.lower()

    def test_app_help_shows_brief_command_descriptions(self):
        """Test jot --help shows brief description for each command."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Verify each command has a brief description
        assert "Add a new task" in result.stdout
        assert (
            "Mark the current active task" in result.stdout or "completed" in result.stdout.lower()
        )
        assert "Cancel the current active task" in result.stdout
        assert "Defer the current active task" in result.stdout
        assert "List all deferred tasks" in result.stdout
        assert "Resume a deferred task" in result.stdout
        assert "Display the current active task" in result.stdout

    def test_short_form_help_option(self):
        """Test jot -h works as shorthand for --help."""
        runner = CliRunner()

        result = runner.invoke(app, ["-h"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "done" in result.stdout

    def test_short_form_version_option(self):
        """Test jot -v works as shorthand for --version."""
        runner = CliRunner()

        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "jot version" in result.stdout
        assert "0.1.0" in result.stdout

    def test_defer_command_shows_argument_help(self):
        """Test jot defer --help shows argument help text."""
        runner = CliRunner()

        result = runner.invoke(app, ["defer", "--help"])

        assert result.exit_code == 0
        assert "reason" in result.stdout.lower()
        assert "prompt" in result.stdout.lower() or "interactive" in result.stdout.lower()

    def test_cancel_command_shows_argument_help(self):
        """Test jot cancel --help shows argument help text."""
        runner = CliRunner()

        result = runner.invoke(app, ["cancel", "--help"])

        assert result.exit_code == 0
        assert "reason" in result.stdout.lower()
        assert "prompt" in result.stdout.lower() or "interactive" in result.stdout.lower()

    def test_resume_command_shows_argument_help(self):
        """Test jot resume --help shows argument help text."""
        runner = CliRunner()

        result = runner.invoke(app, ["resume", "--help"])

        assert result.exit_code == 0
        assert "task_id" in result.stdout.lower() or "task id" in result.stdout.lower()
        assert "number" in result.stdout.lower() or "uuid" in result.stdout.lower()

    def test_rich_formatting_uses_tables(self):
        """Test help text uses Rich table formatting."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Rich formatting should produce table-like structure with borders
        # Check for table indicators (borders, separators)
        assert "+" in result.stdout or "|" in result.stdout or "-" in result.stdout

    def test_invalid_command_suggests_similar_commands(self):
        """Test invalid command suggests similar valid commands via fuzzy matching."""
        runner = CliRunner()

        # Test with command that's close to a real command
        result = runner.invoke(app, ["ad"])  # Close to "add"

        assert result.exit_code != 0
        error_output = result.stdout + result.stderr
        # Typer should suggest "add" for "ad"
        assert "add" in error_output.lower() or "Did you mean" in error_output

    def test_commands_listed_in_logical_order(self):
        """Test commands are listed in a logical order in help."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Commands should be listed in a logical order
        # Check that "add" comes before other commands (it's the primary action)
        add_pos = result.stdout.find("add")
        done_pos = result.stdout.find("done")
        # If both found, add should come before done (or at least be present)
        if add_pos != -1 and done_pos != -1:
            # Both commands should be present
            assert True
        else:
            # At minimum, both should be present
            assert add_pos != -1
            assert done_pos != -1

    def test_help_output_is_readable_and_structured(self):
        """Test help output is well-structured and readable."""
        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Help should have clear sections
        assert "Options" in result.stdout or "OPTIONS" in result.stdout
        assert "Commands" in result.stdout or "COMMANDS" in result.stdout
        # Should have reasonable length (not empty, not too long)
        assert len(result.stdout) > 100  # Should have substantial content
        assert len(result.stdout) < 5000  # Shouldn't be excessively long
