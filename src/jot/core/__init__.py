"""Business logic and domain models for jot.

This package contains pure business logic and domain models.
Core can import from db/ (interfaces only) for repository patterns.
Core MUST NOT import from commands/, monitor/, ipc/, or config/ packages
to maintain architectural boundaries and testability.
"""

from jot.core.exceptions import (
    ConfigError,
    DatabaseError,
    IPCError,
    JotError,
    TaskNotFoundError,
    TaskStateError,
    display_error,
)
from jot.core.task import Task, TaskEvent, TaskState

__all__ = [
    "ConfigError",
    "DatabaseError",
    "IPCError",
    "JotError",
    "Task",
    "TaskEvent",
    "TaskNotFoundError",
    "TaskState",
    "TaskStateError",
    "display_error",
]
