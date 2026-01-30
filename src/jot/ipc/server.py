"""IPC server for monitor process to receive CLI notifications.

This module implements the IPC server that listens on a Unix domain socket
for NDJSON messages from CLI commands. When messages are received, a registered
callback function is invoked to trigger UI updates.

The server runs asynchronously and is designed to integrate with Textual's
async event loop.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import socket
from collections.abc import Callable
from pathlib import Path

from jot.config.paths import get_runtime_dir
from jot.core.exceptions import IPCError
from jot.ipc.events import IPCEvent
from jot.ipc.protocol import deserialize_message

logger = logging.getLogger("jot.ipc.server")

# Check if Unix domain sockets are available
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")

# Configuration constants
_SOCKET_BACKLOG = 5  # Maximum number of pending connections
_BUFFER_SIZE = 4096  # Socket read buffer size (4KB)
_MAX_BUFFER_SIZE = 1024 * 1024  # Maximum buffer size before disconnect (1MB)


class IPCServer:
    """IPC server for monitor process to receive CLI notifications.

    The server listens on a Unix domain socket for NDJSON messages from
    CLI commands. When messages are received, a registered callback function
    is invoked to trigger UI updates.

    The server runs asynchronously and is designed to integrate with Textual's
    async event loop.

    Example:
        >>> async def handle_event(event: IPCEvent, task_id: str) -> None:
        ...     print(f"Received {event} for task {task_id}")
        ...
        >>> server = IPCServer(callback=handle_event)
        >>> await server.start()
        >>> # Server now listening and processing messages...
        >>> # Always call stop() to cleanup resources and remove socket file
        >>> await server.stop()
    """

    def __init__(
        self, callback: Callable[[IPCEvent, str], None], socket_path: Path | None = None
    ) -> None:
        """Initialize IPC server.

        Args:
            callback: Function called when messages received (event, task_id).
                     Can be sync or async.
            socket_path: Optional socket path (uses default if None).

        Raises:
            ValueError: If callback is not callable.
        """
        if not callable(callback):
            raise ValueError("callback must be callable")

        self.callback = callback
        self.socket_path = socket_path or (get_runtime_dir() / "monitor.sock")
        self._server_socket: socket.socket | None = None
        self._running = False
        self._listen_task: asyncio.Task[None] | None = None
        self._connection_tasks: set[asyncio.Task[None]] = set()

    async def start(self) -> None:
        """Start the IPC server.

        Creates Unix domain socket, sets permissions, and begins listening
        for connections. Removes any existing stale socket file.

        Raises:
            IPCError: If socket creation fails
        """
        if not _HAS_AF_UNIX:
            raise IPCError("Unix domain sockets not available on this platform")

        # Remove stale socket file if exists
        if self.socket_path.exists():
            logger.info(f"Removing stale socket file: {self.socket_path}")
            self.socket_path.unlink()

        try:
            # Create Unix domain socket
            self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # type: ignore[attr-defined]
            # Set to non-blocking mode for asyncio
            self._server_socket.setblocking(False)
            self._server_socket.bind(str(self.socket_path))

            # Set restrictive permissions (0600) immediately after bind
            os.chmod(self.socket_path, 0o600)

            # Verify permissions were set correctly
            actual_mode = os.stat(self.socket_path).st_mode & 0o777
            if actual_mode != 0o600:
                raise IPCError(
                    f"Failed to set socket permissions: expected 0600, got {oct(actual_mode)}"
                )

            # Start listening
            self._server_socket.listen(_SOCKET_BACKLOG)
            self._running = True

            # Begin accepting connections
            self._listen_task = asyncio.create_task(self._listen())

        except OSError as e:
            self._running = False
            if self._server_socket:
                self._server_socket.close()
                self._server_socket = None
            # Clean up socket file if it was created
            if self.socket_path.exists():
                with contextlib.suppress(OSError):
                    self.socket_path.unlink()
            raise IPCError(f"Failed to start IPC server: {e}") from e

    async def stop(self) -> None:
        """Stop the IPC server.

        Closes all connections, stops listening, and removes socket file.
        """
        self._running = False

        # Cancel all active connection tasks
        if self._connection_tasks:
            for task in list(self._connection_tasks):
                task.cancel()
            # Wait for all connection tasks to complete
            await asyncio.gather(*self._connection_tasks, return_exceptions=True)
            self._connection_tasks.clear()

        # Cancel listen task
        if self._listen_task:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        # Close listening socket
        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None

        # Remove socket file
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove socket file: {e}")

    async def _listen(self) -> None:
        """Accept connections and handle them concurrently."""
        if not self._server_socket:
            return

        while self._running:
            try:
                # Accept connection (non-blocking with asyncio)
                loop = asyncio.get_event_loop()
                client_socket, _ = await loop.sock_accept(self._server_socket)

                # Handle connection in separate task and track it
                task = asyncio.create_task(self._handle_connection(client_socket))
                self._connection_tasks.add(task)
                # Remove task from set when it completes
                task.add_done_callback(self._connection_tasks.discard)

            except asyncio.CancelledError:
                break
            except OSError as e:
                if self._running:
                    logger.error(f"Error accepting connection: {e}", exc_info=True)
                break

    async def _handle_connection(self, client_socket: socket.socket) -> None:
        """Handle a single client connection.

        Reads NDJSON messages, parses them, and invokes callback.

        Args:
            client_socket: Client socket connection
        """
        try:
            # Set socket to non-blocking mode for asyncio
            client_socket.setblocking(False)
            loop = asyncio.get_event_loop()

            # Buffer for partial lines
            buffer = b""

            # Read lines until connection closes
            while self._running:
                try:
                    # Read data from socket
                    data = await loop.sock_recv(client_socket, _BUFFER_SIZE)
                    if not data:
                        # Connection closed
                        break

                    buffer += data

                    # Check for buffer overflow (DoS protection)
                    if len(buffer) > _MAX_BUFFER_SIZE:
                        logger.warning(
                            f"Buffer overflow: {len(buffer)} bytes, disconnecting client"
                        )
                        break

                    # Process complete lines (NDJSON format: one JSON object per line)
                    while b"\n" in buffer:
                        line_bytes, buffer = buffer.split(b"\n", 1)
                        if not line_bytes:
                            continue

                        line = line_bytes.decode("utf-8")

                        try:
                            # Deserialize NDJSON message
                            message = deserialize_message(line)

                            # Extract event and task_id - catch ValueError for invalid enum
                            try:
                                event = IPCEvent(message["event"])
                            except (ValueError, KeyError) as e:
                                logger.warning(
                                    f"Invalid event type in message: {e} | Raw line: {line[:100]!r}"
                                )
                                continue

                            task_id = message["task_id"]

                            # Invoke callback
                            if asyncio.iscoroutinefunction(self.callback):
                                await self.callback(event, task_id)
                            else:
                                self.callback(event, task_id)

                        except IPCError as e:
                            # Log invalid message with context but continue
                            logger.warning(f"Invalid IPC message: {e} | Raw line: {line[:100]!r}")
                        except Exception as e:
                            # Log callback error but continue
                            logger.error(f"Callback error: {e}", exc_info=True)

                except asyncio.CancelledError:
                    break
                except OSError as e:
                    # Connection closed or error
                    if self._running:
                        logger.info(f"Connection closed: {e}")
                    break

        except Exception as e:
            logger.error(f"Connection handling error: {e}", exc_info=True)
        finally:
            with contextlib.suppress(Exception):
                client_socket.close()
