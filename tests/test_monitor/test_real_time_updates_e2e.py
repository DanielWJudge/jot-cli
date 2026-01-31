"""End-to-end tests for real-time monitor updates via IPC (Story 3.6).

This test suite verifies the complete flow:
CLI command → IPC client → IPC server → MonitorApp callback → Display update
"""

import asyncio
import contextlib
import socket
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from jot.core.task import Task, TaskState
from jot.db.repository import TaskRepository
from jot.ipc.client import notify_monitor
from jot.ipc.events import IPCEvent
from jot.monitor.app import MonitorApp

# Check if Unix domain sockets are available
_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")

# IPC propagation delay - time to wait for IPC message to propagate and be processed
# Set to 200ms (2x the 100ms AC requirement) to ensure reliable test execution
IPC_PROPAGATION_DELAY_S = 0.2


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
class TestRealTimeMonitorUpdatesE2E:
    """End-to-end tests for real-time monitor updates."""

    async def test_cli_add_command_updates_monitor_display(self, temp_db, tmp_path: Path) -> None:
        """Test that CLI 'add' command triggers monitor display update via IPC."""
        # Arrange: Set up monitor app with IPC server
        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            # Start IPC server
            await app.on_mount()

            try:
                # Initially no active task
                assert app._active_task is None
                assert "No active task" in str(app._task_widget.content)

                # Act: Create task via repository and send IPC notification
                repo = TaskRepository()
                task = Task(
                    id=str(uuid.uuid4()),
                    description="E2E test task",
                    state=TaskState.ACTIVE,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                repo.create_task(task)

                # Send IPC notification (simulating CLI command)
                notify_monitor(IPCEvent.TASK_CREATED, task.id)

                # Give IPC server time to process message
                await asyncio.sleep(IPC_PROPAGATION_DELAY_S)

                # Assert: Monitor should have updated display
                assert app._active_task is not None
                assert app._active_task.description == "E2E test task"
                widget_content = str(app._task_widget.content)
                assert "E2E test task" in widget_content
                assert app.title == "jot - E2E test task"

            finally:
                await app.on_unmount()

    async def test_cli_done_command_updates_monitor_display(self, temp_db, tmp_path: Path) -> None:
        """Test that CLI 'done' command triggers monitor display update via IPC."""
        # Arrange: Create active task and set up monitor
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Task to complete",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            # Start IPC server and load initial task
            await app.on_mount()

            try:
                # Verify initial state shows task
                assert app._active_task is not None
                assert app._active_task.description == "Task to complete"

                # Act: Complete task and send IPC notification
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.now(UTC)
                repo.update_task(task)

                notify_monitor(IPCEvent.TASK_COMPLETED, task.id)

                # Give IPC server time to process
                await asyncio.sleep(0.2)

                # Assert: Monitor should show no active task
                assert app._active_task is None
                widget_content = str(app._task_widget.content)
                assert "No active task" in widget_content
                assert app.title == "jot - No active task"

            finally:
                await app.on_unmount()

    async def test_cli_cancel_command_updates_monitor_display(
        self, temp_db, tmp_path: Path
    ) -> None:
        """Test that CLI 'cancel' command triggers monitor display update via IPC."""
        # Arrange: Create active task and set up monitor
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Task to cancel",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            await app.on_mount()

            try:
                # Verify initial state
                assert app._active_task is not None

                # Act: Cancel task and send IPC notification
                task.state = TaskState.CANCELLED
                task.cancelled_at = datetime.now(UTC)
                repo.update_task(task)

                notify_monitor(IPCEvent.TASK_CANCELLED, task.id)

                await asyncio.sleep(0.2)

                # Assert: Monitor should show no active task
                assert app._active_task is None
                widget_content = str(app._task_widget.content)
                assert "No active task" in widget_content

            finally:
                await app.on_unmount()

    async def test_cli_defer_command_updates_monitor_display(self, temp_db, tmp_path: Path) -> None:
        """Test that CLI 'defer' command triggers monitor display update via IPC."""
        # Arrange: Create active task and set up monitor
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Task to defer",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            await app.on_mount()

            try:
                # Verify initial state
                assert app._active_task is not None

                # Act: Defer task and send IPC notification
                task.state = TaskState.DEFERRED
                task.deferred_at = datetime.now(UTC)
                repo.update_task(task)

                notify_monitor(IPCEvent.TASK_DEFERRED, task.id)

                await asyncio.sleep(0.2)

                # Assert: Monitor should show no active task
                assert app._active_task is None
                widget_content = str(app._task_widget.content)
                assert "No active task" in widget_content

            finally:
                await app.on_unmount()

    async def test_multiple_rapid_cli_commands_update_monitor_correctly(
        self, temp_db, tmp_path: Path
    ) -> None:
        """Test that rapid CLI commands update monitor display correctly."""
        # Arrange: Set up monitor
        repo = TaskRepository()

        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            await app.on_mount()

            try:
                # Act: Create, complete, create again (rapid sequence)
                task1 = Task(
                    id=str(uuid.uuid4()),
                    description="First task",
                    state=TaskState.ACTIVE,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                repo.create_task(task1)
                notify_monitor(IPCEvent.TASK_CREATED, task1.id)
                await asyncio.sleep(0.1)

                # Complete task1
                task1.state = TaskState.COMPLETED
                task1.completed_at = datetime.now(UTC)
                repo.update_task(task1)
                notify_monitor(IPCEvent.TASK_COMPLETED, task1.id)
                await asyncio.sleep(0.1)

                # Create task2
                task2 = Task(
                    id=str(uuid.uuid4()),
                    description="Second task",
                    state=TaskState.ACTIVE,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
                repo.create_task(task2)
                notify_monitor(IPCEvent.TASK_CREATED, task2.id)
                await asyncio.sleep(0.2)

                # Assert: Monitor should show task2
                assert app._active_task is not None
                assert app._active_task.description == "Second task"
                widget_content = str(app._task_widget.content)
                assert "Second task" in widget_content

            finally:
                await app.on_unmount()

    async def test_monitor_displays_fresh_data_on_each_ipc_event(
        self, temp_db, tmp_path: Path
    ) -> None:
        """Test that monitor queries fresh data from database on each IPC event."""
        # Arrange: Create task and set up monitor
        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Original description",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        with (
            patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
            patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
        ):
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None

            await app.on_mount()

            try:
                # Verify initial state
                assert app._active_task is not None
                assert app._active_task.description == "Original description"

                # Act: Update task description in database (simulating external change)
                task.description = "Updated description"
                repo.update_task(task)

                # Send IPC event (should query fresh data)
                notify_monitor(IPCEvent.TASK_CREATED, task.id)
                await asyncio.sleep(0.2)

                # Assert: Monitor should show updated description (fresh from DB)
                assert app._active_task is not None
                assert app._active_task.description == "Updated description"
                widget_content = str(app._task_widget.content)
                assert "Updated description" in widget_content

            finally:
                await app.on_unmount()


@pytest.mark.skipif(not _HAS_AF_UNIX, reason="Unix domain sockets not available on this platform")
@pytest.mark.asyncio
async def test_monitor_handles_socket_removed_during_runtime(temp_db, tmp_path: Path) -> None:
    """Test that monitor handles socket file removed during runtime (AC 4)."""
    # Arrange: Create task and set up monitor
    repo = TaskRepository()
    task = Task(
        id=str(uuid.uuid4()),
        description="Test runtime socket removal",
        state=TaskState.ACTIVE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo.create_task(task)

    with (
        patch("jot.ipc.server.get_runtime_dir", return_value=tmp_path),
        patch("jot.ipc.client.get_runtime_dir", return_value=tmp_path),
    ):
        app = MonitorApp()
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None

        await app.on_mount()

        try:
            # Verify IPC server started and socket exists
            socket_path = tmp_path / "monitor.sock"
            assert socket_path.exists()

            # Act: Remove socket file while monitor is running
            socket_path.unlink()

            # Monitor should continue functioning even with socket removed
            # Display should still work
            assert app._active_task is not None
            assert app._active_task.description == "Test runtime socket removal"

            # Try to send IPC message - should fail gracefully (no crash)
            with contextlib.suppress(Exception):
                notify_monitor(IPCEvent.TASK_COMPLETED, task.id)
                # Expected to fail - socket is gone

            # Monitor should still be functional
            widget_content = str(app._task_widget.content)
            assert "Test runtime socket removal" in widget_content

        finally:
            await app.on_unmount()
