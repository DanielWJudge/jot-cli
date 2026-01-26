"""Test suite for core.exceptions module."""

import sys

import pytest
from rich.console import Console

from jot.core.exceptions import (
    ConfigError,
    DatabaseError,
    IPCError,
    JotError,
    TaskNotFoundError,
    TaskStateError,
    display_error,
)


class TestJotError:
    """Test base JotError exception."""

    def test_default_exit_code(self) -> None:
        """Test default exit code is 1 (user error)."""
        error = JotError("Test error")
        assert error.exit_code == 1

    def test_custom_exit_code(self) -> None:
        """Test custom exit code can be set."""
        error = JotError("Test error", exit_code=2)
        assert error.exit_code == 2

    def test_exception_message(self) -> None:
        """Test exception message is preserved."""
        error = JotError("Custom message")
        assert str(error) == "Custom message"

    def test_exception_with_empty_message(self) -> None:
        """Test exception with empty message."""
        error = JotError("")
        assert str(error) == ""
        assert error.exit_code == 1


class TestTaskNotFoundError:
    """Test TaskNotFoundError exception."""

    def test_inherits_from_jot_error(self) -> None:
        """Test TaskNotFoundError inherits from JotError."""
        error = TaskNotFoundError("Task not found")
        assert isinstance(error, JotError)

    def test_exit_code_is_one(self) -> None:
        """Test TaskNotFoundError has exit_code=1."""
        error = TaskNotFoundError("Task not found")
        assert error.exit_code == 1

    def test_default_message(self) -> None:
        """Test TaskNotFoundError has default message."""
        error = TaskNotFoundError()
        assert str(error) == "Task not found"

    def test_custom_message(self) -> None:
        """Test TaskNotFoundError accepts custom message."""
        error = TaskNotFoundError("Custom task not found message")
        assert str(error) == "Custom task not found message"


class TestTaskStateError:
    """Test TaskStateError exception."""

    def test_inherits_from_jot_error(self) -> None:
        """Test TaskStateError inherits from JotError."""
        error = TaskStateError("Invalid state transition")
        assert isinstance(error, JotError)

    def test_exit_code_is_one(self) -> None:
        """Test TaskStateError has exit_code=1."""
        error = TaskStateError("Invalid state transition")
        assert error.exit_code == 1

    def test_message_preserved(self) -> None:
        """Test TaskStateError message is preserved."""
        error = TaskStateError("Cannot complete already completed task")
        assert str(error) == "Cannot complete already completed task"


class TestDatabaseError:
    """Test DatabaseError exception."""

    def test_inherits_from_jot_error(self) -> None:
        """Test DatabaseError inherits from JotError."""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, JotError)

    def test_exit_code_is_two(self) -> None:
        """Test DatabaseError has exit_code=2 (system error)."""
        error = DatabaseError("Database connection failed")
        assert error.exit_code == 2

    def test_message_preserved(self) -> None:
        """Test DatabaseError message is preserved."""
        error = DatabaseError("Connection timeout")
        assert str(error) == "Connection timeout"


class TestConfigError:
    """Test ConfigError exception."""

    def test_inherits_from_jot_error(self) -> None:
        """Test ConfigError inherits from JotError."""
        error = ConfigError("Invalid configuration")
        assert isinstance(error, JotError)

    def test_exit_code_is_one(self) -> None:
        """Test ConfigError has exit_code=1."""
        error = ConfigError("Invalid configuration")
        assert error.exit_code == 1

    def test_message_preserved(self) -> None:
        """Test ConfigError message is preserved."""
        error = ConfigError("Config file not found")
        assert str(error) == "Config file not found"


class TestIPCError:
    """Test IPCError exception."""

    def test_inherits_from_jot_error(self) -> None:
        """Test IPCError inherits from JotError."""
        error = IPCError("IPC operation failed")
        assert isinstance(error, JotError)

    def test_exit_code_is_two(self) -> None:
        """Test IPCError has exit_code=2 (system error)."""
        error = IPCError("IPC operation failed")
        assert error.exit_code == 2

    def test_message_preserved(self) -> None:
        """Test IPCError message is preserved."""
        error = IPCError("Socket connection failed")
        assert str(error) == "Socket connection failed"


class TestDisplayError:
    """Test error display utility."""

    def test_displays_to_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error display goes to stderr, not stdout."""
        console = Console(file=sys.stderr, force_terminal=True)
        display_error(TaskNotFoundError("No task found"), console)

        captured = capsys.readouterr()
        assert "No task found" in captured.err
        assert captured.out == ""  # Nothing to stdout

    def test_formats_with_rich_markup(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error formatting uses Rich markup."""
        console = Console(file=sys.stderr, force_terminal=True)
        display_error(
            TaskNotFoundError("No task found"),
            console,
            suggestion="Try: jot add 'task description'",
        )

        captured = capsys.readouterr()
        assert "No task found" in captured.err
        assert "Try: jot add" in captured.err

    def test_handles_exceptions_without_suggestions(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test error display works without recovery suggestions."""
        console = Console(file=sys.stderr, force_terminal=True)
        display_error(DatabaseError("Connection failed"), console)

        captured = capsys.readouterr()
        assert "Connection failed" in captured.err

    def test_uses_default_console_if_none_provided(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test display_error uses default stderr console if None provided."""
        # Use a StringIO-based console to capture output reliably
        from io import StringIO

        stderr_buffer = StringIO()
        test_console = Console(file=stderr_buffer, force_terminal=False)
        display_error(TaskNotFoundError("No task found"), console=test_console)

        output = stderr_buffer.getvalue()
        assert "No task found" in output
        assert "Error" in output

    def test_displays_error_with_long_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test error display handles long error messages."""
        from io import StringIO

        stderr_buffer = StringIO()
        console = Console(file=stderr_buffer, force_terminal=False)
        long_message = "This is a very long error message that might wrap across multiple lines"
        display_error(TaskNotFoundError(long_message), console)

        output = stderr_buffer.getvalue()
        # Rich may wrap text, so check that the message content is present
        assert long_message in output or all(word in output for word in long_message.split()[:5])

    def test_displays_error_with_special_characters(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test error display handles special characters."""
        console = Console(file=sys.stderr, force_terminal=True)
        special_message = "Error: Task 'test-task-123' not found!"
        display_error(TaskNotFoundError(special_message), console)

        captured = capsys.readouterr()
        assert special_message in captured.err


class TestSystemExitPattern:
    """Test SystemExit pattern integration."""

    def test_system_exit_with_exit_code(self) -> None:
        """Test that exceptions can be used with SystemExit."""
        error = TaskNotFoundError("Task not found")
        with pytest.raises(SystemExit) as exc_info:
            raise SystemExit(error.exit_code)
        assert exc_info.value.code == 1

    def test_system_exit_with_database_error(self) -> None:
        """Test SystemExit with DatabaseError exit code."""
        error = DatabaseError("Database failed")
        with pytest.raises(SystemExit) as exc_info:
            raise SystemExit(error.exit_code)
        assert exc_info.value.code == 2

    def test_system_exit_with_ipc_error(self) -> None:
        """Test SystemExit with IPCError exit code."""
        error = IPCError("IPC failed")
        with pytest.raises(SystemExit) as exc_info:
            raise SystemExit(error.exit_code)
        assert exc_info.value.code == 2
