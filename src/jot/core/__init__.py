"""Business logic and domain models for jot.

This package contains pure business logic and domain models.
Core can import from db/ (interfaces only) for repository patterns.
Core MUST NOT import from commands/, monitor/, ipc/, or config/ packages
to maintain architectural boundaries and testability.

The theme module provides centralized theme constants and formatting functions
for consistent design language between Rich (CLI) and Textual (monitor) interfaces.
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
from jot.core.theme import (
    TaskColors,
    TaskEmoji,
    TextStyles,
    format_task_state,
    get_color_for_capability,
    get_emoji,
    get_textual_style_for_state,
    should_use_color,
)

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
    "TaskColors",
    "TaskEmoji",
    "TextStyles",
    "display_error",
    "format_task_state",
    "get_color_for_capability",
    "get_emoji",
    "get_textual_style_for_state",
    "should_use_color",
]
