"""Theme module for consistent visuals across CLI and monitor.

This module provides centralized theme constants and formatting functions
for consistent design language between Rich (CLI) and Textual (monitor) interfaces.
"""

import logging
import os
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from jot.core.task import Task, TaskState

logger = logging.getLogger(__name__)

# Type alias for state input (accepts both TaskState enum and string)
type StateInput = "TaskState | str"


class TaskColors:
    """Color constants for task states.

    Colors are designed to be color-blind friendly and work across
    terminal capabilities (8-color, 256-color, truecolor).

    Attributes:
        ACTIVE: Bright cyan for current task
        COMPLETED: Green for completed tasks
        CANCELLED: Red for cancelled tasks
        DEFERRED: Yellow/orange for deferred tasks
        MUTED: Dim gray for metadata/secondary info
    """

    ACTIVE = "cyan"
    COMPLETED = "green"
    CANCELLED = "red"
    DEFERRED = "yellow"
    MUTED = "dim"


class TaskEmoji:
    """Emoji constants for task states and UI elements.

    Emojis provide visual landmarks and work alongside colors
    for multi-modal state indication.

    Attributes:
        ACTIVE: Target emoji for active task
        COMPLETED: Checkmark for completed tasks
        CANCELLED: Cross mark for cancelled tasks
        DEFERRED: Pause button for deferred tasks
        STREAK: Fire for streak indicators
        DATE: Calendar for date indicators
        CELEBRATE: Party for celebrations
    """

    ACTIVE = "🎯"
    COMPLETED = "✅"
    CANCELLED = "❌"
    DEFERRED = "⏸️"
    STREAK = "🔥"
    DATE = "📅"
    CELEBRATE = "🎉"


class TextStyles:
    """Rich style strings for consistent text formatting.

    Styles use Rich markup syntax and can be combined.
    Example: [bold cyan]text[/] or [strike green]text[/]

    Attributes:
        heading: Bold for headings
        task_current: Bold cyan for current task
        task_completed: Strikethrough green for completed
        task_cancelled: Dim red for cancelled
        task_deferred: Dim yellow for deferred tasks
        metadata: Dim for metadata/secondary info
    """

    heading = "bold"
    task_current = "bold cyan"
    task_completed = "strike green"
    task_cancelled = "dim red"
    task_deferred = "dim yellow"
    metadata = "dim"


# ASCII fallback mapping for emoji
_ASCII_EMOJI_MAP = {
    TaskEmoji.ACTIVE: "[ACTIVE]",
    TaskEmoji.COMPLETED: "[DONE]",
    TaskEmoji.CANCELLED: "[CANCELLED]",
    TaskEmoji.DEFERRED: "[DEFERRED]",
    TaskEmoji.STREAK: "[STREAK]",
    TaskEmoji.DATE: "[DATE]",
    TaskEmoji.CELEBRATE: "[CELEBRATE]",
}

# State to emoji mapping
_STATE_EMOJI_MAP = {
    "active": TaskEmoji.ACTIVE,
    "completed": TaskEmoji.COMPLETED,
    "cancelled": TaskEmoji.CANCELLED,
    "deferred": TaskEmoji.DEFERRED,
}

# State to color mapping
_STATE_COLOR_MAP = {
    "active": TaskColors.ACTIVE,
    "completed": TaskColors.COMPLETED,
    "cancelled": TaskColors.CANCELLED,
    "deferred": TaskColors.DEFERRED,
}

# State to style mapping
_STATE_STYLE_MAP = {
    "active": TextStyles.task_current,
    "completed": TextStyles.task_completed,
    "cancelled": TextStyles.task_cancelled,
    "deferred": TextStyles.task_deferred,
}

# 8-color fallback mapping for standard terminals
_8COLOR_FALLBACK = {
    "cyan": "blue",  # Standard 8-color terminals don't have cyan, use blue as closest match
    "yellow": "yellow",  # Yellow works in 8-color
    "green": "green",  # Green works in 8-color
    "red": "red",  # Red works in 8-color
}


def get_emoji(state: StateInput, ascii_only: bool = False) -> str:
    """Get emoji for task state with ASCII fallback.

    Args:
        state: TaskState enum value or state string (e.g., "active", "completed").
            If TaskState enum, uses state.value automatically.
        ascii_only: If True, return ASCII indicator instead of emoji

    Returns:
        Emoji string or ASCII indicator

    Examples:
        >>> from jot.core.task import TaskState
        >>> get_emoji(TaskState.ACTIVE)
        '🎯'
        >>> get_emoji("active")
        '🎯'
        >>> get_emoji("active", ascii_only=True)
        '[ACTIVE]'
    """
    # Handle TaskState enum
    state_str = state.value if hasattr(state, "value") else str(state)

    emoji = _STATE_EMOJI_MAP.get(state_str, TaskEmoji.ACTIVE)
    if ascii_only:
        return _ASCII_EMOJI_MAP.get(emoji, emoji)
    return emoji


def format_task_state(task: "Task", ascii_only: bool = False) -> str:
    """Format task state with emoji and Rich styling.

    Args:
        task: Task instance to format
        ascii_only: If True, use ASCII indicators instead of emoji

    Returns:
        Rich markup string with emoji and styled description
    """
    state = task.state.value
    emoji = get_emoji(state, ascii_only=ascii_only)
    style = _STATE_STYLE_MAP.get(state, TextStyles.metadata)

    return f"{emoji} [{style}]{task.description}[/]"


def get_textual_style_for_state(state: StateInput) -> dict[str, str | bool]:
    """Get Textual style dictionary for task state.

    Args:
        state: TaskState enum value or state string (e.g., "active", "completed").
            If TaskState enum, uses state.value automatically.

    Returns:
        Dictionary with Textual style attributes compatible with Textual Style objects.
        Keys: "foreground" (str), "bold" (bool), "strike" (bool), "dim" (bool)

    Examples:
        >>> from jot.core.task import TaskState
        >>> from textual.style import Style
        >>> style_dict = get_textual_style_for_state(TaskState.ACTIVE)
        >>> style = Style(**style_dict)  # Works with Textual Style
        >>> style_dict = get_textual_style_for_state("completed")
        >>> style = Style(**style_dict)  # Also works with string
    """
    # Handle TaskState enum
    state_str = state.value if hasattr(state, "value") else str(state)

    # Validate state
    if state_str not in _STATE_COLOR_MAP:
        logger.warning(
            f"Unknown task state '{state_str}', defaulting to MUTED color. "
            f"Valid states: {list(_STATE_COLOR_MAP.keys())}"
        )

    color = _STATE_COLOR_MAP.get(state_str, TaskColors.MUTED)
    style_dict: dict[str, str | bool] = {"foreground": color}

    # Add additional style attributes based on state
    # Textual Style expects boolean values, not strings
    if state_str == "active":
        style_dict["bold"] = True
    elif state_str == "completed":
        style_dict["strike"] = True
    elif state_str in ("cancelled", "deferred"):
        style_dict["dim"] = True

    return style_dict


def should_use_color(console: Console | None = None) -> bool:
    """Check if colors should be used based on terminal capabilities and NO_COLOR.

    Respects the NO_COLOR environment variable (https://no-color.org) - when set,
    colors are disabled regardless of terminal capabilities.

    Args:
        console: Optional Rich Console instance. If None, creates a new one.

    Returns:
        True if colors should be used, False otherwise
    """
    # Respect NO_COLOR environment variable (no-color.org standard)
    if os.getenv("NO_COLOR"):
        return False

    if console is None:
        console = Console()

    # Check terminal color system capability
    color_system = console.color_system
    return color_system is not None


def get_color_for_capability(
    console: Console,
    default_color: str,
) -> str | None:
    """Get color appropriate for terminal capabilities.

    Args:
        console: Rich Console instance
        default_color: Default color name

    Returns:
        Color name appropriate for terminal capabilities, or None if no color

    Examples:
        >>> from rich.console import Console
        >>> console = Console()
        >>> # In 8-color terminal, cyan falls back to blue
        >>> get_color_for_capability(console, "cyan")
        'blue'
        >>> # In 256-color or truecolor terminal, returns original
        >>> get_color_for_capability(console, "cyan")
        'cyan'
        >>> # With NO_COLOR environment variable, returns None
        >>> import os
        >>> os.environ["NO_COLOR"] = "1"
        >>> get_color_for_capability(console, "cyan")
        None
    """
    if not should_use_color(console):
        return None

    color_system = console.color_system

    if color_system == "standard":  # 8-color
        return _8COLOR_FALLBACK.get(default_color, default_color)
    elif color_system in ("256", "truecolor"):
        return default_color  # Full palette available
    else:  # Monochrome or None
        return None
