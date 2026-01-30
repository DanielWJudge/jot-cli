"""Inter-process communication for jot.

This package contains IPC protocols and communication logic between
the CLI process and the monitor window process.
The ipc package can ONLY import from core.exceptions and config.paths.
It MUST NOT import from commands/ or monitor/.
"""

from jot.core.exceptions import IPCError
from jot.ipc.events import IPCEvent
from jot.ipc.protocol import deserialize_message, serialize_message

__all__ = ["IPCEvent", "serialize_message", "deserialize_message", "IPCError"]
