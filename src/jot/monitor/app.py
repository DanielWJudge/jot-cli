"""Monitor application using Textual framework.

This module provides the main monitor window application that displays
the current active task in a persistent terminal window.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from jot.core.task import Task
from jot.core.theme import TaskEmoji, get_textual_style_for_state
from jot.db.repository import TaskRepository


class MonitorApp(App):  # type: ignore[misc]
    """Monitor application for displaying current active task.

    The monitor window shows the current active task prominently and
    can be exited with 'q' key or Ctrl+C.
    """

    TITLE = "jot - No active task"
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        """Initialize MonitorApp."""
        super().__init__()
        self._active_task: Task | None = None
        self._task_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the app widgets."""
        self._task_widget = Static("No active task")
        yield self._task_widget

    async def on_mount(self) -> None:
        """Query database for active task when app mounts."""
        repo = TaskRepository()
        self._active_task = repo.get_active_task()
        self._update_display()

    def _update_display(self) -> None:
        """Update the display based on current active task."""
        if self._task_widget is None:
            return

        if self._active_task is None:
            self._task_widget.update("No active task")
            self.title = "jot - No active task"
        else:
            # Use theme module for emoji and styling
            emoji = TaskEmoji.ACTIVE
            style_dict = get_textual_style_for_state("active")

            # Display task with emoji and apply styling
            display_text = f"{emoji} {self._active_task.description}"
            self._task_widget.update(display_text)

            # Apply Textual styles from theme module
            if "foreground" in style_dict:
                self._task_widget.styles.foreground = style_dict["foreground"]
            if style_dict.get("bold"):
                self._task_widget.styles.bold = True
            if style_dict.get("dim"):
                self._task_widget.styles.opacity = 0.7

            self.title = f"jot - {self._active_task.description}"

    def action_quit(self) -> None:
        """Handle quit action."""
        self.exit()
