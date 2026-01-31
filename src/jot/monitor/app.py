"""Monitor application using Textual framework.

This module provides the main monitor window application that displays
the current active task in a persistent terminal window.
"""

import logging
import signal
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from jot.core.task import Task
from jot.core.theme import TaskEmoji, get_textual_style_for_state
from jot.db.repository import TaskRepository
from jot.ipc.events import IPCEvent
from jot.ipc.server import IPCServer

logger = logging.getLogger("jot.monitor.app")


class MonitorApp(App):  # type: ignore[misc]
    """Monitor application for displaying current active task.

    The monitor window shows the current active task prominently and
    can be exited with 'q' key or Ctrl+C.
    """

    TITLE = "jot - No active task"
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
    ]

    def __init__(self) -> None:
        """Initialize monitor with empty state. Database query happens on mount."""
        super().__init__()
        self._active_task: Task | None = None
        self._task_widget: Static | None = None
        self._ipc_server: IPCServer | None = None
        self._original_sigint_handler: Any = None

    def compose(self) -> ComposeResult:
        """Compose the app widgets."""
        self._task_widget = Static("No active task")
        yield self._task_widget

    async def on_mount(self) -> None:
        """Query database for active task and start IPC server when app mounts."""
        # Set up signal handlers for graceful Ctrl+C shutdown
        self._setup_signal_handlers()

        # Start IPC server (creates socket file for detection)
        self._ipc_server = IPCServer(callback=self._handle_ipc_event)
        try:
            await self._ipc_server.start()
            logger.info("IPC server started successfully")
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")
            # Continue anyway - monitor can work without IPC for this story

        # Query database for initial active task
        repo = TaskRepository()
        self._active_task = repo.get_active_task()
        self._update_display()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful Ctrl+C shutdown."""
        # Store original handler to restore later
        self._original_sigint_handler = signal.getsignal(signal.SIGINT)

        def handle_sigint(_signum: int, _frame: object) -> None:
            """Handle Ctrl+C by initiating graceful shutdown."""
            logger.info("Received SIGINT (Ctrl+C), shutting down...")
            self.exit()

        # Register SIGINT handler (Ctrl+C)
        signal.signal(signal.SIGINT, handle_sigint)

    def _handle_ipc_event(self, event: IPCEvent, task_id: str) -> None:
        """Handle IPC events from CLI commands (placeholder for Story 3.6).

        Args:
            event: The IPC event type
            task_id: The task ID associated with the event
        """
        # Placeholder for Story 3.6 - real-time updates
        # For now, just log that we received an event
        logger.info(f"Received IPC event: {event} for task {task_id}")

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

            # Apply Textual styles from theme module with error handling
            try:
                if "foreground" in style_dict:
                    foreground_value = style_dict["foreground"]
                    if isinstance(foreground_value, str):
                        self._task_widget.styles.color = foreground_value
                if style_dict.get("bold"):
                    self._task_widget.styles.text_style = "bold"
                if style_dict.get("dim"):
                    self._task_widget.styles.opacity = 0.7
            except (KeyError, ValueError, AttributeError) as e:
                logger.warning(f"Failed to apply theme styles: {e}")

            self.title = f"jot - {self._active_task.description}"

    async def action_quit(self) -> None:
        """Handle quit action with cleanup."""
        logger.info("Quit action triggered")
        self.exit()

    async def on_unmount(self) -> None:
        """Clean up resources when app is unmounting."""
        # Stop IPC server and remove socket file
        if self._ipc_server:
            try:
                await self._ipc_server.stop()
                logger.info("IPC server stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping IPC server: {e}")

        # Restore original signal handler
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)
