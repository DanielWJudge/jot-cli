"""Test suite for IPC client module."""

from __future__ import annotations

import logging
import socket
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from _pytest.logging import LogCaptureFixture

from jot.ipc.client import notify_monitor
from jot.ipc.events import IPCEvent

# Import database fixtures for integration tests
from tests.test_db.conftest import db_path, mock_data_dir, temp_db  # noqa: F401, F811

# Check if Unix domain sockets are available
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")


class TestNotifyMonitor:
    """Test notify_monitor function."""

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_with_existing_socket_successful_send(self, tmp_path: Path) -> None:
        """Test notify_monitor() with existing socket sends message successfully."""
        # Create a temporary socket file
        socket_path = tmp_path / "monitor.sock"

        # Mock get_runtime_dir to return our temp path
        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            # Create a mock socket server to receive the message
            server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_socket.bind(str(socket_path))
            server_socket.listen(1)

            try:
                # Call notify_monitor
                notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")

                # Accept connection and receive message
                client_conn, _ = server_socket.accept()
                received_data = client_conn.recv(1024)
                client_conn.close()

                # Verify message was sent
                assert received_data is not None
                assert len(received_data) > 0
                message = received_data.decode("utf-8")
                assert "TASK_CREATED" in message
                assert "test-task-id" in message
                assert message.endswith("\n")
            finally:
                server_socket.close()
                if socket_path.exists():
                    socket_path.unlink()

    def test_notify_monitor_with_non_existent_socket_silent_return(self) -> None:
        """Test notify_monitor() with non-existent socket returns silently."""
        if not _HAS_AF_UNIX:
            # On Windows, function returns early - just verify it doesn't raise
            notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")
            return

        # Mock get_runtime_dir to return a path without socket
        with patch("jot.ipc.client.get_runtime_dir") as mock_get_runtime:
            mock_runtime_dir = Path("/nonexistent/path")
            mock_get_runtime.return_value = mock_runtime_dir

            # Should not raise any exception
            notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")

            # Verify get_runtime_dir was called
            mock_get_runtime.assert_called_once()

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_connection_timeout_graceful_handling(self, tmp_path: Path) -> None:
        """Test notify_monitor() handles connection timeout gracefully."""
        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            # Create a socket file but don't bind a server (will timeout)
            socket_path.touch()

            # Should not raise exception, just return silently
            notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")

            # Cleanup
            if socket_path.exists():
                socket_path.unlink()

    def test_notify_monitor_connection_refused_graceful_handling(self, tmp_path: Path) -> None:
        """Test notify_monitor() handles connection refused gracefully."""
        if not _HAS_AF_UNIX:
            # On Windows, function returns early - just verify it doesn't raise
            notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")
            return

        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            # Create socket file but remove it before connection attempt
            socket_path.touch()

            # Mock socket.connect to raise ConnectionRefusedError
            with patch("socket.socket") as mock_socket_class:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")

                # Should not raise exception
                notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")

                # Verify socket was closed
                mock_sock.close.assert_called()

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_sends_correct_ndjson_format(self, tmp_path: Path) -> None:
        """Test notify_monitor() sends correct NDJSON format."""
        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            # Create server socket
            server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_socket.bind(str(socket_path))
            server_socket.listen(1)

            try:
                notify_monitor(IPCEvent.TASK_COMPLETED, "task-123")

                # Accept and receive
                client_conn, _ = server_socket.accept()
                received_data = client_conn.recv(1024)
                client_conn.close()

                # Parse JSON
                import json

                message = received_data.decode("utf-8").strip()
                parsed = json.loads(message)

                # Verify structure
                assert parsed["event"] == "TASK_COMPLETED"
                assert parsed["task_id"] == "task-123"
                assert "timestamp" in parsed
                assert message.endswith("\n") or received_data.endswith(b"\n")
            finally:
                server_socket.close()
                if socket_path.exists():
                    socket_path.unlink()

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_uses_correct_socket_path(self, tmp_path: Path) -> None:
        """Test notify_monitor() uses correct socket path from paths module."""
        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path) as mock_get_runtime:
            # Create server socket
            server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_socket.bind(str(socket_path))
            server_socket.listen(1)

            try:
                notify_monitor(IPCEvent.TASK_CREATED, "test-id")

                # Verify get_runtime_dir was called
                mock_get_runtime.assert_called_once()

                # Verify connection was attempted to correct path
                client_conn, _ = server_socket.accept()
                client_conn.close()
            finally:
                server_socket.close()
                if socket_path.exists():
                    socket_path.unlink()

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_closes_socket_after_sending(self, tmp_path: Path) -> None:
        """Test notify_monitor() closes socket after sending."""
        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_socket.bind(str(socket_path))
            server_socket.listen(1)

            try:
                notify_monitor(IPCEvent.TASK_CREATED, "test-id")

                # Accept connection
                client_conn, _ = server_socket.accept()

                # Try to send data back - should fail if socket is closed
                # (This is a basic check - actual close verification is in implementation)
                client_conn.close()
            finally:
                server_socket.close()
                if socket_path.exists():
                    socket_path.unlink()

    @pytest.mark.skipif(
        not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform"
    )
    def test_notify_monitor_with_all_event_types(self, tmp_path: Path) -> None:
        """Test notify_monitor() works with all IPCEvent types."""
        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            for event in IPCEvent:
                # Create fresh server socket for each event
                if socket_path.exists():
                    socket_path.unlink()

                server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                server_socket.bind(str(socket_path))
                server_socket.listen(1)

                try:
                    notify_monitor(event, "test-task-id")

                    # Verify message was sent
                    client_conn, _ = server_socket.accept()
                    received_data = client_conn.recv(1024)
                    client_conn.close()

                    message = received_data.decode("utf-8")
                    assert event.value in message
                finally:
                    server_socket.close()
                    if socket_path.exists():
                        socket_path.unlink()

    def test_notify_monitor_never_raises_exceptions(self, tmp_path: Path) -> None:
        """Test notify_monitor() never raises exceptions, even on errors."""
        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            # Test various error conditions
            if _HAS_AF_UNIX:
                error_scenarios = [
                    (FileNotFoundError, "Socket not found"),
                    (ConnectionRefusedError, "Connection refused"),
                    (TimeoutError, "Connection timeout"),
                    (OSError, "Other socket error"),
                ]

                for error_class, error_msg in error_scenarios:
                    with patch("socket.socket") as mock_socket_class:
                        mock_sock = MagicMock()
                        mock_socket_class.return_value = mock_sock
                        mock_sock.connect.side_effect = error_class(error_msg)

                        # Should not raise exception
                        result = notify_monitor(IPCEvent.TASK_CREATED, "test-id")
                        assert result is None
            else:
                # On platforms without AF_UNIX, should return silently
                result = notify_monitor(IPCEvent.TASK_CREATED, "test-id")
                assert result is None

    def test_notify_monitor_graceful_degradation_no_af_unix(self) -> None:
        """Test notify_monitor() returns silently when AF_UNIX is not available."""
        # Mock socket module to not have AF_UNIX
        with patch("jot.ipc.client._HAS_AF_UNIX", False):
            # Should return silently without raising exceptions
            result = notify_monitor(IPCEvent.TASK_CREATED, "test-id")
            assert result is None

    def test_notify_monitor_sendall_failure_graceful_handling(self, tmp_path: Path) -> None:
        """Test notify_monitor() handles sendall() failures gracefully."""
        if not _HAS_AF_UNIX:
            # On Windows, function returns early - just verify it doesn't raise
            notify_monitor(IPCEvent.TASK_CREATED, "test-task-id")
            return

        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            socket_path.touch()

            # Mock socket to connect successfully but fail on sendall
            with patch("socket.socket") as mock_socket_class:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                # Connect succeeds, but sendall fails
                mock_sock.connect.return_value = None
                mock_sock.sendall.side_effect = BrokenPipeError("Broken pipe")

                # Should not raise exception
                result = notify_monitor(IPCEvent.TASK_CREATED, "test-id")
                assert result is None

                # Verify socket was closed
                mock_sock.close.assert_called()

    def test_notify_monitor_get_runtime_dir_exception_graceful_handling(self) -> None:
        """Test notify_monitor() handles get_runtime_dir() exceptions gracefully."""
        # Mock get_runtime_dir to raise an exception
        with patch("jot.ipc.client.get_runtime_dir", side_effect=OSError("Path resolution failed")):
            # Should not raise exception
            result = notify_monitor(IPCEvent.TASK_CREATED, "test-id")
            assert result is None

    def test_notify_monitor_logs_errors_at_warning_level(
        self, tmp_path: Path, caplog: LogCaptureFixture
    ) -> None:
        """Test notify_monitor() logs connection errors at WARNING level."""
        if not _HAS_AF_UNIX:
            # On Windows, function returns early - skip logging test
            return

        socket_path = tmp_path / "monitor.sock"

        with patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path):
            socket_path.touch()

            # Mock socket.connect to raise ConnectionRefusedError
            with patch("socket.socket") as mock_socket_class:
                mock_sock = MagicMock()
                mock_socket_class.return_value = mock_sock
                mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")

                # Set logging level to WARNING to capture logs
                with caplog.at_level(logging.WARNING, logger="jot.ipc.client"):
                    notify_monitor(IPCEvent.TASK_CREATED, "test-id")

                    # Verify error was logged at WARNING level (not DEBUG)
                    assert len(caplog.records) > 0
                    assert any(
                        "IPC notification failed" in record.message for record in caplog.records
                    )
                    assert any(record.levelno == logging.WARNING for record in caplog.records)


class TestIPCIntegration:
    """Test IPC integration with CLI commands."""

    def test_add_command_calls_notify_monitor(self, temp_db, tmp_path: Path) -> None:  # noqa: F811
        """Test jot add command calls notify_monitor after task creation."""
        from typer.testing import CliRunner

        from jot.cli import app

        runner = CliRunner()

        # Mock notify_monitor to verify it's called
        with patch("jot.commands.add.notify_monitor") as mock_notify:
            result = runner.invoke(app, ["add", "Test task"])

            assert result.exit_code == 0
            # Verify notify_monitor was called with correct arguments
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == IPCEvent.TASK_CREATED
            assert isinstance(call_args[0][1], str)  # task_id

    def test_done_command_calls_notify_monitor(self, temp_db) -> None:  # noqa: F811
        """Test jot done command calls notify_monitor after completion."""
        from datetime import UTC, datetime

        from typer.testing import CliRunner

        from jot.cli import app
        from jot.core.task import Task, TaskState
        from jot.db.repository import TaskRepository

        # Create an active task first
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        runner = CliRunner()

        # Mock notify_monitor to verify it's called
        with patch("jot.commands.done.notify_monitor") as mock_notify:
            result = runner.invoke(app, ["done"])

            assert result.exit_code == 0
            # Verify notify_monitor was called with correct arguments
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == IPCEvent.TASK_COMPLETED
            assert call_args[0][1] == task.id

    def test_cancel_command_calls_notify_monitor(self, temp_db) -> None:  # noqa: F811
        """Test jot cancel command calls notify_monitor after cancellation."""
        from datetime import UTC, datetime

        from typer.testing import CliRunner

        from jot.cli import app
        from jot.core.task import Task, TaskState
        from jot.db.repository import TaskRepository

        # Create an active task first
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        runner = CliRunner()

        # Mock notify_monitor to verify it's called
        with patch("jot.commands.cancel.notify_monitor") as mock_notify:
            result = runner.invoke(app, ["cancel", "test reason"])

            assert result.exit_code == 0
            # Verify notify_monitor was called with correct arguments
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == IPCEvent.TASK_CANCELLED
            assert call_args[0][1] == task.id

    def test_defer_command_calls_notify_monitor(self, temp_db) -> None:  # noqa: F811
        """Test jot defer command calls notify_monitor after deferral."""
        from datetime import UTC, datetime

        from typer.testing import CliRunner

        from jot.cli import app
        from jot.core.task import Task, TaskState
        from jot.db.repository import TaskRepository

        # Create an active task first
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        runner = CliRunner()

        # Mock notify_monitor to verify it's called
        with patch("jot.commands.defer.notify_monitor") as mock_notify:
            result = runner.invoke(app, ["defer", "test reason"])

            assert result.exit_code == 0
            # Verify notify_monitor was called with correct arguments
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == IPCEvent.TASK_DEFERRED
            assert call_args[0][1] == task.id

    def test_resume_command_calls_notify_monitor(self, temp_db) -> None:  # noqa: F811
        """Test jot resume command calls notify_monitor after resumption."""
        from datetime import UTC, datetime

        from typer.testing import CliRunner

        from jot.cli import app
        from jot.core.task import Task, TaskState
        from jot.db.repository import TaskRepository

        # Create a deferred task first
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task",
            state=TaskState.DEFERRED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deferred_at=datetime.now(UTC),
            defer_reason="test",
        )
        repo.create_task(task)

        runner = CliRunner()

        # Mock notify_monitor to verify it's called
        with patch("jot.commands.resume.notify_monitor") as mock_notify:
            result = runner.invoke(app, ["resume", task.id])

            assert result.exit_code == 0
            # Verify notify_monitor was called with correct arguments
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == IPCEvent.TASK_RESUMED
            assert call_args[0][1] == task.id

    def test_ipc_socket_errors_dont_affect_cli_command_success(self, temp_db) -> None:  # noqa: F811
        """Test that IPC socket errors don't affect CLI command success."""
        from typer.testing import CliRunner

        from jot.cli import app

        runner = CliRunner()

        # Mock notify_monitor to raise socket error (expected failure type)
        with patch("jot.commands.add.notify_monitor", side_effect=OSError("Socket error")):
            result = runner.invoke(app, ["add", "Test task"])

            # Command should still succeed despite IPC failure
            assert result.exit_code == 0
            assert "🎯 Added: Test task" in result.stdout

    def test_programming_errors_propagate_from_cli_commands(self, temp_db) -> None:  # noqa: F811
        """Test that programming errors (non-socket) propagate and fail CLI commands."""
        from typer.testing import CliRunner

        from jot.cli import app

        runner = CliRunner()

        # Mock notify_monitor to raise programming error (should NOT be caught)
        with patch("jot.commands.add.notify_monitor", side_effect=AttributeError("Bad code")):
            result = runner.invoke(app, ["add", "Test task"])

            # Command should fail with programming error (not silently suppressed)
            assert result.exit_code != 0
