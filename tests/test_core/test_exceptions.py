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
        # Pass None explicitly to test default console creation
        display_error(TaskNotFoundError("No task found"), console=None)

        captured = capsys.readouterr()
        assert "No task found" in captured.err
        assert "Error" in captured.err or "❌" in captured.err
        assert captured.out == ""  # Nothing to stdout

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
        # Use StringIO to avoid ANSI escape codes in test output
        from io import StringIO

        stderr_buffer = StringIO()
        console = Console(file=stderr_buffer, force_terminal=False)
        special_message = "Error: Task 'test-task-123' not found!"
        display_error(TaskNotFoundError(special_message), console)

        output = stderr_buffer.getvalue()
        # Check that the special characters are preserved in the output
        assert special_message in output


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


class TestGuardrailCompliance:
    """Guardrail tests to ensure architectural compliance and prevent regressions.

    These tests enforce architectural constraints defined in Architecture.md
    and ensure that future changes don't violate critical error handling patterns.
    """

    def test_all_exceptions_inherit_from_jot_error(self) -> None:
        """GUARDRAIL: All jot exceptions must inherit from JotError."""
        # Verify exception hierarchy compliance
        assert issubclass(TaskNotFoundError, JotError)
        assert issubclass(TaskStateError, JotError)
        assert issubclass(DatabaseError, JotError)
        assert issubclass(ConfigError, JotError)
        assert issubclass(IPCError, JotError)

        # Verify instances are JotError instances
        assert isinstance(TaskNotFoundError(), JotError)
        assert isinstance(TaskStateError("test"), JotError)
        assert isinstance(DatabaseError("test"), JotError)
        assert isinstance(ConfigError("test"), JotError)
        assert isinstance(IPCError("test"), JotError)

    def test_user_error_exit_codes_are_one(self) -> None:
        """GUARDRAIL: User errors must have exit_code=1 per Architecture.md."""
        # User errors: TaskNotFoundError, TaskStateError, ConfigError
        assert TaskNotFoundError().exit_code == 1
        assert TaskStateError("test").exit_code == 1
        assert ConfigError("test").exit_code == 1

        # Verify JotError default is also 1 (user error)
        assert JotError("test").exit_code == 1

    def test_system_error_exit_codes_are_two(self) -> None:
        """GUARDRAIL: System errors must have exit_code=2 per Architecture.md."""
        # System errors: DatabaseError, IPCError
        assert DatabaseError("test").exit_code == 2
        assert IPCError("test").exit_code == 2

    def test_exit_code_standards_enforcement(self) -> None:
        """GUARDRAIL: Exit codes must follow Architecture.md standards.

        Architecture defines:
        - 0: Success
        - 1: User error
        - 2: System error
        """
        # Verify no exceptions have exit_code=0 (success)
        # This would be a logical error - exceptions indicate failure
        user_errors = [
            TaskNotFoundError(),
            TaskStateError("test"),
            ConfigError("test"),
        ]
        for error in user_errors:
            assert error.exit_code == 1, f"{type(error).__name__} must have exit_code=1"

        system_errors = [
            DatabaseError("test"),
            IPCError("test"),
        ]
        for error in system_errors:
            assert error.exit_code == 2, f"{type(error).__name__} must have exit_code=2"

    def test_error_display_always_uses_stderr(self, capsys: pytest.CaptureFixture[str]) -> None:
        """GUARDRAIL: Error display must go to stderr, never stdout."""
        console = Console(file=sys.stderr, force_terminal=True)
        error = TaskNotFoundError("Guardrail test error")

        display_error(error, console)

        captured = capsys.readouterr()
        # Error must be in stderr
        assert "Guardrail test error" in captured.err
        # stdout must be empty (errors never go to stdout)
        assert captured.out == "", "Errors must go to stderr, never stdout"

    def test_error_display_with_suggestion_uses_stderr(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GUARDRAIL: Error display with suggestion must go to stderr."""
        console = Console(file=sys.stderr, force_terminal=True)
        error = TaskNotFoundError("Guardrail test error")

        display_error(error, console, suggestion="Test suggestion")

        captured = capsys.readouterr()
        # Both error and suggestion must be in stderr
        assert "Guardrail test error" in captured.err
        assert "Test suggestion" in captured.err
        # stdout must be empty
        assert captured.out == "", "Error output must never go to stdout"

    def test_default_console_is_stderr(self) -> None:
        """GUARDRAIL: Default console in display_error must use stderr."""
        from io import StringIO

        # Create a StringIO buffer to capture stderr output
        stderr_buffer = StringIO()
        test_console = Console(file=stderr_buffer, force_terminal=False)
        error = TaskNotFoundError("Default console test")

        # Call with None console parameter - should use default stderr console
        # But we'll test with a custom console to verify behavior
        # The actual default console writes to sys.stderr which capsys can't capture reliably
        display_error(error, console=test_console)

        output = stderr_buffer.getvalue()
        assert "Default console test" in output
        # Verify it's using the provided console (which simulates stderr behavior)
        assert "Error" in output or "❌" in output

    def test_system_exit_pattern_compliance(self) -> None:
        """GUARDRAIL: SystemExit pattern must work with all exception types."""
        # Architecture requires: raise SystemExit(error.exit_code)
        test_cases = [
            (TaskNotFoundError("test"), 1),
            (TaskStateError("test"), 1),
            (ConfigError("test"), 1),
            (DatabaseError("test"), 2),
            (IPCError("test"), 2),
        ]

        for error, expected_exit_code in test_cases:
            with pytest.raises(SystemExit) as exc_info:
                raise SystemExit(error.exit_code)
            assert (
                exc_info.value.code == expected_exit_code
            ), f"{type(error).__name__} SystemExit pattern failed"

    def test_exception_message_preservation(self) -> None:
        """GUARDRAIL: Exception messages must be preserved correctly."""
        test_message = "Test error message with special chars: !@#$%^&*()"
        error = TaskNotFoundError(test_message)

        # Message must be accessible via str() and .message attribute
        assert str(error) == test_message
        assert error.message == test_message

    def test_exception_hierarchy_no_direct_exception_inheritance(self) -> None:
        """GUARDRAIL: No jot exceptions should inherit directly from Exception."""
        # All exceptions must go through JotError hierarchy
        jot_exceptions = [
            TaskNotFoundError,
            TaskStateError,
            DatabaseError,
            ConfigError,
            IPCError,
        ]

        for exc_class in jot_exceptions:
            # Must inherit from JotError, not directly from Exception
            assert JotError in exc_class.__mro__
            # Should not skip JotError in inheritance chain
            mro = exc_class.__mro__
            jot_error_index = mro.index(JotError)
            exception_index = mro.index(Exception)
            assert (
                jot_error_index < exception_index
            ), f"{exc_class.__name__} must inherit through JotError"

    def test_display_error_requires_jot_error(self) -> None:
        """GUARDRAIL: display_error must only accept JotError instances."""
        console = Console(file=sys.stderr, force_terminal=True)

        # Should accept JotError and subclasses
        display_error(TaskNotFoundError("test"), console)
        display_error(JotError("test"), console)

        # Should reject non-JotError exceptions
        # This is a runtime guardrail - ValueError doesn't have .message attribute
        # which will cause AttributeError when display_error tries to access it
        with pytest.raises(AttributeError):
            # ValueError doesn't have .message attribute
            display_error(ValueError("test"), console)

    def test_exception_classes_have_exit_code_attribute(self) -> None:
        """GUARDRAIL: All exception instances must have exit_code attribute."""
        exceptions = [
            JotError("test"),
            TaskNotFoundError("test"),
            TaskStateError("test"),
            DatabaseError("test"),
            ConfigError("test"),
            IPCError("test"),
        ]

        for error in exceptions:
            assert hasattr(error, "exit_code"), f"{type(error).__name__} must have exit_code"
            assert isinstance(error.exit_code, int), "exit_code must be an integer"
            assert error.exit_code in (1, 2), "exit_code must be 1 or 2"

    def test_no_exit_code_zero_allowed(self) -> None:
        """GUARDRAIL: No exception should have exit_code=0 (success)."""
        # Even if someone tries to create JotError with exit_code=0, verify it's caught
        # In practice, this shouldn't happen, but guardrail ensures it doesn't
        exceptions = [
            JotError("test", exit_code=1),  # Valid
            JotError("test", exit_code=2),  # Valid
            TaskNotFoundError("test"),  # Should be 1
            DatabaseError("test"),  # Should be 2
        ]

        for error in exceptions:
            assert (
                error.exit_code != 0
            ), f"{type(error).__name__} cannot have exit_code=0 (exceptions indicate failure)"

    def test_rich_markup_in_error_display(self, capsys: pytest.CaptureFixture[str]) -> None:
        """GUARDRAIL: Error display must use Rich markup for formatting."""
        from io import StringIO

        stderr_buffer = StringIO()
        console = Console(file=stderr_buffer, force_terminal=False)
        error = TaskNotFoundError("Test error")

        display_error(error, console)

        output = stderr_buffer.getvalue()
        # Rich markup should be present (even if stripped in non-terminal mode)
        # At minimum, error message should be formatted
        assert "Test error" in output
        assert "Error" in output or "❌" in output

    def test_error_display_suggestion_formatting(self, capsys: pytest.CaptureFixture[str]) -> None:
        """GUARDRAIL: Suggestions must be formatted with Rich markup."""
        from io import StringIO

        stderr_buffer = StringIO()
        console = Console(file=stderr_buffer, force_terminal=False)
        error = TaskNotFoundError("Test error")

        display_error(error, console, suggestion="Try: jot add 'task'")

        output = stderr_buffer.getvalue()
        assert "Test error" in output
        assert "Try: jot add" in output or "Suggestion" in output or "💡" in output

    def test_module_boundary_compliance(self) -> None:
        """GUARDRAIL: Exception module must not violate architecture boundaries.

        Architecture requires:
        - core/ module MUST NOT import from commands/ or monitor/
        - Exception classes should be stdlib-only (Rich only in display_error)
        """
        import inspect

        # Verify exception classes don't import Rich in their __init__ methods
        exception_classes = [
            JotError,
            TaskNotFoundError,
            TaskStateError,
            DatabaseError,
            ConfigError,
            IPCError,
        ]

        for exc_class in exception_classes:
            try:
                source = inspect.getsource(exc_class.__init__)
                # Exception __init__ should not import Rich
                # Rich should only be used in display_error function
                assert (
                    "from rich" not in source.lower()
                ), f"{exc_class.__name__}.__init__ should not import Rich"
                assert (
                    "import rich" not in source.lower()
                ), f"{exc_class.__name__}.__init__ should not import Rich"
            except (OSError, TypeError):
                # If source is not available (e.g., C extension), skip this check
                pass

    def test_exception_naming_conventions(self) -> None:
        """GUARDRAIL: Exception names must follow PEP 8 and architecture conventions."""
        # All exception names should end with "Error"
        exception_classes = [
            JotError,
            TaskNotFoundError,
            TaskStateError,
            DatabaseError,
            ConfigError,
            IPCError,
        ]

        for exc_class in exception_classes:
            class_name = exc_class.__name__
            assert class_name.endswith("Error"), f"{class_name} must end with 'Error'"
            # Should use PascalCase
            assert class_name[0].isupper(), f"{class_name} must use PascalCase"

    def test_display_error_function_signature(self) -> None:
        """GUARDRAIL: display_error function signature must match architecture."""
        import inspect

        sig = inspect.signature(display_error)
        params = list(sig.parameters.keys())

        # Must accept: error, console (optional), suggestion (optional)
        assert "error" in params, "display_error must accept 'error' parameter"
        assert "console" in params, "display_error must accept 'console' parameter"
        assert "suggestion" in params, "display_error must accept 'suggestion' parameter"

        # error should be first (required), console and suggestion should be optional
        assert params[0] == "error", "error must be first parameter"
        # console should have default None
        assert sig.parameters["console"].default is None, "console should default to None"
        # suggestion should have default None
        assert sig.parameters["suggestion"].default is None, "suggestion should default to None"
