"""IPC event types for CLI-to-Monitor communication.

This module defines the IPCEvent enum which represents all possible
event types that can be sent between the CLI process and the monitor
window process.

All event names use SCREAMING_SNAKE_CASE convention.
"""

from __future__ import annotations

from enum import Enum


class IPCEvent(str, Enum):
    """IPC event types for CLI-to-Monitor communication.

    All event names use SCREAMING_SNAKE_CASE convention.
    """

    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_CANCELLED = "TASK_CANCELLED"
    TASK_DEFERRED = "TASK_DEFERRED"
    TASK_RESUMED = "TASK_RESUMED"
    CONFIG_CHANGED = "CONFIG_CHANGED"


__all__ = ["IPCEvent"]
