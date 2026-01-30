"""Test suite for IPC server module."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import stat
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from jot.ipc.events import IPCEvent

# Check if Unix domain sockets are available
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")

# Import server class (will be created)
try:
    from jot.ipc.server import IPCServer
except ImportError:
    IPCServer = None  # type: ignore[assignment, misc]


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerInitialization:
    """Test IPCServer initialization."""

    async def test_init_with_default_socket_path(self, tmp_path: Path) -> None:
        """Test IPCServer initialization with default socket path."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        with patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path):
            server = IPCServer(callback=callback)

            assert server.callback == callback
            assert server.socket_path == tmp_path / "monitor.sock"
            assert server._server_socket is None
            assert server._running is False

    async def test_init_with_custom_socket_path(self) -> None:
        """Test IPCServer initialization with custom socket path."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        custom_path = Path("/tmp/custom.sock")
        server = IPCServer(callback=callback, socket_path=custom_path)

        assert server.callback == callback
        assert server.socket_path == custom_path
        assert server._server_socket is None
        assert server._running is False

    async def test_init_stores_callback_reference(self) -> None:
        """Test IPCServer stores callback reference."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        server = IPCServer(callback=callback)

        assert server.callback == callback

    async def test_init_rejects_non_callable_callback(self) -> None:
        """Test IPCServer rejects non-callable callback."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        with pytest.raises(ValueError, match="callback must be callable"):
            IPCServer(callback="not a function")  # type: ignore[arg-type]


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerStart:
    """Test IPCServer start() method."""

    async def test_start_creates_socket_file(self, tmp_path: Path) -> None:
        """Test start() creates socket file."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            assert socket_path.exists()
            assert server._running is True
        finally:
            await server.stop()

    async def test_start_sets_socket_permissions_0600(self, tmp_path: Path) -> None:
        """Test start() sets socket file permissions to 0600."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Check permissions (Unix only)
            if hasattr(os, "stat"):
                file_stat = os.stat(socket_path)
                actual_mode = stat.S_IMODE(file_stat.st_mode)
                assert actual_mode == 0o600, f"Expected 0600, got {oct(actual_mode)}"
        finally:
            await server.stop()

    async def test_start_removes_stale_socket_file(self, tmp_path: Path) -> None:
        """Test start() removes existing stale socket file."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        # Create stale socket file
        socket_path.touch()
        assert socket_path.exists()

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Socket file should still exist (recreated)
            assert socket_path.exists()
            # But it should be a socket now, not a regular file
        finally:
            await server.stop()

    async def test_start_binds_to_socket_path(self, tmp_path: Path) -> None:
        """Test start() binds socket to configured path."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Try to connect to socket (should succeed if bound)
            test_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            test_sock.settimeout(0.1)
            try:
                test_sock.connect(str(socket_path))
                # Connection succeeded - socket is bound
                test_sock.close()
            except (ConnectionRefusedError, FileNotFoundError):
                pytest.fail("Socket not bound correctly")
            finally:
                test_sock.close()
        finally:
            await server.stop()

    async def test_start_begins_listening(self, tmp_path: Path) -> None:
        """Test start() begins listening for connections."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Give server a moment to start listening
            await asyncio.sleep(0.01)

            # Try to connect - should succeed if listening
            test_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            test_sock.settimeout(0.1)
            try:
                test_sock.connect(str(socket_path))
                test_sock.close()
            except (ConnectionRefusedError, FileNotFoundError):
                pytest.fail("Server not listening")
            finally:
                test_sock.close()
        finally:
            await server.stop()


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerStop:
    """Test IPCServer stop() method."""

    async def test_stop_closes_socket(self, tmp_path: Path) -> None:
        """Test stop() closes listening socket."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        # Verify socket exists
        assert socket_path.exists()

        await server.stop()

        # Socket file should be removed
        assert not socket_path.exists()
        assert server._server_socket is None
        assert server._running is False

    async def test_stop_removes_socket_file(self, tmp_path: Path) -> None:
        """Test stop() removes socket file."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()
        assert socket_path.exists()

        await server.stop()

        assert not socket_path.exists()

    async def test_stop_idempotent(self, tmp_path: Path) -> None:
        """Test stop() can be called multiple times safely."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        # Call stop multiple times
        await server.stop()
        await server.stop()
        await server.stop()

        assert not socket_path.exists()
        assert server._server_socket is None


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerConnectionHandling:
    """Test IPCServer connection handling."""

    async def test_server_accepts_connections(self, tmp_path: Path) -> None:
        """Test server accepts incoming connections."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Connect to server
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))

            # Give server time to accept connection
            await asyncio.sleep(0.1)

            # Connection should be accepted (no exception)
            client_sock.close()
        finally:
            await server.stop()

    async def test_server_reads_ndjson_messages(self, tmp_path: Path) -> None:
        """Test server reads NDJSON messages from connections."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Send NDJSON message
            from jot.ipc.protocol import serialize_message

            message = serialize_message(IPCEvent.TASK_CREATED, "test-task-123")

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(message.encode("utf-8"))
            client_sock.close()

            # Give server time to process message
            await asyncio.sleep(0.2)

            # Callback should have been called
            callback.assert_called_once()
        finally:
            await server.stop()

    async def test_server_invokes_callback_with_correct_args(self, tmp_path: Path) -> None:
        """Test server invokes callback with correct event and task_id."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            event = IPCEvent.TASK_COMPLETED
            task_id = "test-task-456"

            message = serialize_message(event, task_id)

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(message.encode("utf-8"))
            client_sock.close()

            # Give server time to process
            await asyncio.sleep(0.2)

            # Verify callback called with correct arguments
            callback.assert_called_once()
            call_args = callback.call_args[0]
            assert call_args[0] == event
            assert call_args[1] == task_id
        finally:
            await server.stop()

    async def test_server_handles_multiple_connections(self, tmp_path: Path) -> None:
        """Test server handles multiple concurrent connections."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Send multiple messages from different connections
            for i in range(3):
                message = serialize_message(IPCEvent.TASK_CREATED, f"task-{i}")

                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.settimeout(1.0)
                client_sock.connect(str(socket_path))
                client_sock.sendall(message.encode("utf-8"))
                client_sock.close()

            # Give server time to process all messages
            await asyncio.sleep(0.3)

            # Callback should have been called 3 times
            assert callback.call_count == 3
        finally:
            await server.stop()


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerErrorHandling:
    """Test IPCServer error handling."""

    async def test_invalid_messages_logged_and_ignored(self, tmp_path: Path, caplog) -> None:
        """Test invalid messages are logged and ignored (server continues)."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            with caplog.at_level(logging.WARNING, logger="jot.ipc.server"):
                # Send invalid JSON
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.settimeout(1.0)
                client_sock.connect(str(socket_path))
                client_sock.sendall(b"invalid json\n")
                client_sock.close()

                # Give server time to process
                await asyncio.sleep(0.2)

                # Callback should not have been called
                callback.assert_not_called()

                # Warning should be logged
                assert len(caplog.records) > 0
                assert any("Invalid" in record.message for record in caplog.records)
        finally:
            await server.stop()

    async def test_invalid_event_type_logged_and_ignored(self, tmp_path: Path, caplog) -> None:
        """Test messages with invalid event types are logged and ignored."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            with caplog.at_level(logging.WARNING, logger="jot.ipc.server"):
                # Send message with invalid event type
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.settimeout(1.0)
                client_sock.connect(str(socket_path))
                # Valid JSON but invalid event type
                client_sock.sendall(
                    b'{"event":"INVALID_EVENT","task_id":"123","timestamp":"2026-01-29T12:00:00Z"}\n'
                )
                client_sock.close()

                # Give server time to process
                await asyncio.sleep(0.2)

                # Callback should not have been called
                callback.assert_not_called()

                # Warning should be logged with context
                assert len(caplog.records) > 0
                assert any(
                    "Invalid" in record.message and "Raw line" in record.message
                    for record in caplog.records
                )
        finally:
            await server.stop()

    async def test_buffer_overflow_protection(self, tmp_path: Path, caplog) -> None:
        """Test server disconnects clients that send too much data without newlines."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            with caplog.at_level(logging.WARNING, logger="jot.ipc.server"):
                # Send huge data without newline to trigger buffer overflow
                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.settimeout(1.0)
                client_sock.connect(str(socket_path))

                # Send data in chunks to exceed buffer limit
                chunk = b"x" * 100000  # 100KB chunks
                for _ in range(12):  # Total 1.2MB > 1MB limit
                    try:
                        client_sock.sendall(chunk)
                        await asyncio.sleep(0.01)
                    except BrokenPipeError:
                        break  # Server closed connection

                client_sock.close()

                # Give server time to process
                await asyncio.sleep(0.2)

                # Warning should be logged about buffer overflow
                assert any("Buffer overflow" in record.message for record in caplog.records)
        finally:
            await server.stop()

    async def test_callback_exceptions_dont_crash_server(self, tmp_path: Path) -> None:
        """Test callback exceptions don't crash server."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        # Callback that raises exception
        async def failing_callback(event: IPCEvent, task_id: str) -> None:
            raise ValueError("Callback error")

        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=failing_callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Send valid message
            message = serialize_message(IPCEvent.TASK_CREATED, "test-task")

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(message.encode("utf-8"))
            client_sock.close()

            # Give server time to process
            await asyncio.sleep(0.2)

            # Server should still be running (not crashed)
            assert server._running is True

            # Send another message - server should still work
            client_sock2 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock2.settimeout(1.0)
            client_sock2.connect(str(socket_path))
            client_sock2.sendall(message.encode("utf-8"))
            client_sock2.close()

            await asyncio.sleep(0.2)
            assert server._running is True
        finally:
            await server.stop()

    async def test_server_handles_all_event_types(self, tmp_path: Path) -> None:
        """Test server handles all IPCEvent types."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Send all event types
            for event in IPCEvent:
                message = serialize_message(event, "test-task")

                client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                client_sock.settimeout(1.0)
                client_sock.connect(str(socket_path))
                client_sock.sendall(message.encode("utf-8"))
                client_sock.close()

                await asyncio.sleep(0.1)

            # Callback should have been called for each event
            assert callback.call_count == len(IPCEvent)
        finally:
            await server.stop()


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerLifecycle:
    """Test IPCServer lifecycle."""

    async def test_start_stop_lifecycle(self, tmp_path: Path) -> None:
        """Test complete server lifecycle (start → process → stop)."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)

        # Start server
        await server.start()
        assert server._running is True
        assert socket_path.exists()

        # Send message
        from jot.ipc.protocol import serialize_message

        message = serialize_message(IPCEvent.TASK_CREATED, "test-task")

        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.settimeout(1.0)
        client_sock.connect(str(socket_path))
        client_sock.sendall(message.encode("utf-8"))
        client_sock.close()

        await asyncio.sleep(0.2)
        callback.assert_called_once()

        # Stop server
        await server.stop()
        assert server._running is False
        assert not socket_path.exists()

    async def test_sync_callback_supported(self, tmp_path: Path) -> None:
        """Test server supports synchronous callbacks."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback_calls = []

        def sync_callback(event: IPCEvent, task_id: str) -> None:
            callback_calls.append((event, task_id))

        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=sync_callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            message = serialize_message(IPCEvent.TASK_CREATED, "test-task")

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(message.encode("utf-8"))
            client_sock.close()

            await asyncio.sleep(0.2)

            assert len(callback_calls) == 1
            assert callback_calls[0][0] == IPCEvent.TASK_CREATED
            assert callback_calls[0][1] == "test-task"
        finally:
            await server.stop()


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestIPCServerEdgeCases:
    """Test IPCServer edge cases and advanced scenarios."""

    async def test_server_handles_partial_messages_split_across_reads(self, tmp_path: Path) -> None:
        """Test server handles messages split across multiple socket reads."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Create a message and split it in half
            full_message = serialize_message(IPCEvent.TASK_CREATED, "test-task")
            message_bytes = full_message.encode("utf-8")
            midpoint = len(message_bytes) // 2
            first_half = message_bytes[:midpoint]
            second_half = message_bytes[midpoint:]

            # Send message in two parts
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(first_half)
            await asyncio.sleep(0.05)  # Small delay to ensure separate reads
            client_sock.sendall(second_half)
            client_sock.close()

            # Give server time to process
            await asyncio.sleep(0.2)

            # Callback should have been called once with complete message
            callback.assert_called_once()
            call_args = callback.call_args[0]
            assert call_args[0] == IPCEvent.TASK_CREATED
            assert call_args[1] == "test-task"
        finally:
            await server.stop()

    async def test_server_handles_multiple_messages_in_single_connection(
        self, tmp_path: Path
    ) -> None:
        """Test server handles multiple NDJSON messages in a single connection."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Send multiple messages in one connection
            messages = [
                serialize_message(IPCEvent.TASK_CREATED, "task-1"),
                serialize_message(IPCEvent.TASK_COMPLETED, "task-2"),
                serialize_message(IPCEvent.TASK_CANCELLED, "task-3"),
            ]
            combined = "".join(messages)

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(combined.encode("utf-8"))
            client_sock.close()

            # Give server time to process all messages
            await asyncio.sleep(0.3)

            # Callback should have been called 3 times
            assert callback.call_count == 3
            assert callback.call_args_list[0][0][0] == IPCEvent.TASK_CREATED
            assert callback.call_args_list[1][0][0] == IPCEvent.TASK_COMPLETED
            assert callback.call_args_list[2][0][0] == IPCEvent.TASK_CANCELLED
        finally:
            await server.stop()

    async def test_server_handles_client_disconnect_gracefully(self, tmp_path: Path) -> None:
        """Test server handles abrupt client disconnection gracefully."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            # Connect and immediately disconnect without sending complete message
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(b'{"event": "TASK_CREATED", "task_id": "incomplete')
            client_sock.close()  # Abrupt disconnect

            # Give server time to handle disconnect
            await asyncio.sleep(0.2)

            # Server should still be running
            assert server._running is True
            # Callback should not have been called (incomplete message)
            callback.assert_not_called()
        finally:
            await server.stop()

    async def test_server_can_restart_after_stop(self, tmp_path: Path) -> None:
        """Test server can be started again after being stopped."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)

        # First start/stop cycle
        await server.start()
        assert server._running is True
        await server.stop()
        assert server._running is False
        assert not socket_path.exists()

        # Second start/stop cycle
        await server.start()
        assert server._running is True
        assert socket_path.exists()

        try:
            # Verify server still works
            from jot.ipc.protocol import serialize_message

            message = serialize_message(IPCEvent.TASK_CREATED, "test-task")
            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(message.encode("utf-8"))
            client_sock.close()

            await asyncio.sleep(0.2)
            callback.assert_called_once()
        finally:
            await server.stop()

    async def test_server_handles_empty_lines_gracefully(self, tmp_path: Path) -> None:
        """Test server handles empty lines (blank NDJSON lines) gracefully."""
        if IPCServer is None:
            pytest.skip("IPCServer not yet implemented")

        callback = AsyncMock()
        socket_path = tmp_path / "monitor.sock"

        server = IPCServer(callback=callback, socket_path=socket_path)
        await server.start()

        try:
            from jot.ipc.protocol import serialize_message

            # Send valid message, empty line, then another valid message
            messages = [
                serialize_message(IPCEvent.TASK_CREATED, "task-1"),
                "\n",  # Empty line
                serialize_message(IPCEvent.TASK_COMPLETED, "task-2"),
            ]
            combined = "".join(messages)

            client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_sock.settimeout(1.0)
            client_sock.connect(str(socket_path))
            client_sock.sendall(combined.encode("utf-8"))
            client_sock.close()

            await asyncio.sleep(0.2)

            # Should process both valid messages, skip empty line
            assert callback.call_count == 2
        finally:
            await server.stop()
