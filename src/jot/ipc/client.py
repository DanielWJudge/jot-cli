"""IPC client for CLI-to-Monitor communication.

This module implements the fire-and-forget IPC client that allows CLI commands
to notify the monitor process of task state changes without blocking or waiting
for responses.

The client uses Unix domain sockets and follows a graceful degradation pattern:
if the monitor is not running or connection fails, the CLI continues normally.
"""

from __future__ import annotations

import logging
import socket

from jot.config.paths import get_runtime_dir
from jot.ipc.events import IPCEvent
from jot.ipc.protocol import serialize_message

logger = logging.getLogger("jot.ipc.client")

# Check if Unix domain sockets are available
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")


def notify_monitor(event: IPCEvent, task_id: str) -> None:
    """Notify monitor process of task state change.

    Sends an NDJSON message to the monitor socket using fire-and-forget
    pattern. If the monitor is not running or connection fails, this
    function returns silently without raising exceptions.

    Args:
        event: IPC event type (from IPCEvent enum)
        task_id: Task identifier (string, typically UUID format)

    Returns:
        None (always succeeds, even if monitor unavailable)

    Note:
        This function never raises exceptions. All errors are caught
        and logged. FileNotFoundError (socket missing) is silent,
        other connection errors are logged at WARNING level.
    """
    # Check if Unix domain sockets are available
    if not _HAS_AF_UNIX:
        # Unix sockets not available on this platform - return silently
        return

    # Get socket path from paths module (protect against path resolution failures)
    try:
        runtime_dir = get_runtime_dir()
        socket_path = runtime_dir / "monitor.sock"
    except OSError as e:
        logger.warning(f"Failed to resolve runtime directory: {e}")
        return

    sock = None
    try:
        # Create Unix domain socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # type: ignore[attr-defined]
        sock.settimeout(0.1)  # 100ms timeout

        # Connect to socket (will raise FileNotFoundError if socket doesn't exist)
        sock.connect(str(socket_path))

        # Serialize and send NDJSON message
        message = serialize_message(event, task_id)
        sock.sendall(message.encode("utf-8"))

    except FileNotFoundError:
        # Socket doesn't exist (monitor not running) - expected, return silently
        pass
    except (ConnectionRefusedError, TimeoutError) as e:
        # Connection failures - monitor may be starting/stopping
        logger.warning(f"IPC notification failed (monitor may be unavailable): {e}")
    except OSError as e:
        # Other socket errors (permissions, etc.)
        logger.warning(f"IPC notification failed: {e}")
    finally:
        # Always close socket
        if sock:
            sock.close()
