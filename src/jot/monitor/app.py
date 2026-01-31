"""Monitor application using Textual framework.

This module provides the main monitor window application that displays
the current active task in a persistent terminal window.
"""

import asyncio
import logging
import signal
import time
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

# Performance monitoring constants
_IPC_LATENCY_WARNING_MS = 100  # Warn if IPC event handling exceeds 100ms (NFR5)


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

        # Start IPC server with retry logic for robustness
        self._ipc_server = IPCServer(callback=self._handle_ipc_event)
        await self._start_ipc_server_with_retry()

        # Query database for initial active task
        repo = TaskRepository()
        self._active_task = repo.get_active_task()
        self._update_display()

    async def _start_ipc_server_with_retry(self, max_attempts: int = 3) -> None:
        """Start IPC server with retry logic for robustness.

        Args:
            max_attempts: Maximum number of startup attempts
        """
        # Early return if no server to start
        ipc_server = self._ipc_server
        if ipc_server is None:
            return

        for attempt in range(1, max_attempts + 1):
            try:
                await ipc_server.start()
                logger.info(f"IPC server started successfully on attempt {attempt}")
                return
            except Exception as e:
                logger.error(f"Failed to start IPC server (attempt {attempt}/{max_attempts}): {e}")
                if attempt < max_attempts:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(0.5 * attempt)
                else:
                    # All attempts failed - continue in degraded mode
                    logger.warning(
                        "IPC server failed to start after all attempts. "
                        "Monitor will function but real-time updates disabled."
                    )
                    self._ipc_server = None

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

    async def _handle_ipc_event(self, event: IPCEvent, task_id: str) -> None:
        """Handle IPC events from CLI commands for real-time updates.

        When an IPC event is received, this method queries the database
        fresh (source of truth) and updates the display accordingly.

        Uses asyncio.to_thread to run blocking DB queries without blocking
        Textual's event loop, ensuring responsive UI.

        Args:
            event: The IPC event type (TASK_CREATED, TASK_COMPLETED, etc.)
            task_id: The task ID associated with the event
        """
        start_time = time.perf_counter()
        current_task_id = self._active_task.id if self._active_task else None

        logger.info(
            f"Received IPC event: {event} for task {task_id} " f"(current_task={current_task_id})"
        )

        try:
            # Run blocking database query in thread pool to avoid blocking event loop
            # This ensures Textual remains responsive while querying SQLite
            def query_db() -> Task | None:
                repo = TaskRepository()
                return repo.get_active_task()

            self._active_task = await asyncio.to_thread(query_db)

            # Update display with fresh data
            self._update_display()

            # Measure and log latency for performance monitoring (NFR5)
            latency_ms = (time.perf_counter() - start_time) * 1000
            if latency_ms > _IPC_LATENCY_WARNING_MS:
                logger.warning(
                    f"IPC event handling exceeded {_IPC_LATENCY_WARNING_MS}ms: "
                    f"{latency_ms:.2f}ms for {event}"
                )
            else:
                logger.debug(f"IPC event handled in {latency_ms:.2f}ms")

        except Exception as e:
            # Log error with full context but continue functioning (graceful degradation)
            logger.error(
                f"Error handling IPC event {event} for task {task_id} "
                f"(current_task={current_task_id}): {e}",
                exc_info=True,
            )
            # Keep current display - don't crash monitor

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
