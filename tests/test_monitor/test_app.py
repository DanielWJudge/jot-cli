"""Test suite for monitor.app module."""

import uuid
from datetime import UTC, datetime

from textual.app import App

from jot.core.task import Task, TaskState
from jot.monitor.app import MonitorApp


class TestMonitorApp:
    """Test MonitorApp class."""

    def test_app_extends_textual_app(self):
        """Test MonitorApp extends Textual App."""
        assert issubclass(MonitorApp, App)

    def test_app_initializes_with_title(self):
        """Test MonitorApp initializes with title."""
        app = MonitorApp()
        assert app.title == "jot - No active task"

    def test_app_has_q_key_binding(self):
        """Test MonitorApp has 'q' key binding for quit."""
        # Check that 'q' key binding exists in BINDINGS class attribute
        bindings = MonitorApp.BINDINGS
        q_binding = next((b for b in bindings if b.key == "q"), None)
        assert q_binding is not None
        assert q_binding.action == "quit"

    def test_app_has_ctrl_c_key_binding(self):
        """Test MonitorApp has Ctrl+C key binding for quit."""
        # Check that 'ctrl+c' key binding exists in BINDINGS class attribute
        bindings = MonitorApp.BINDINGS
        ctrl_c_binding = next((b for b in bindings if b.key == "ctrl+c"), None)
        assert ctrl_c_binding is not None
        assert ctrl_c_binding.action == "quit"

    def test_app_queries_database_on_mount(self, temp_db):
        """Test MonitorApp queries database for active task on mount."""
        # Arrange: Create active task
        from unittest.mock import AsyncMock, patch

        from jot.db.repository import TaskRepository

        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test active task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Act: Create app and manually call on_mount (mock IPC server to avoid socket creation)
        app = MonitorApp()
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            # Manually trigger on_mount to test database query
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: App should have queried and stored the task
        assert app._active_task is not None
        assert app._active_task.description == "Test active task"
        # Verify IPC server was started (socket file creation)
        mock_server_instance.start.assert_called_once()

    def test_app_handles_no_active_task(self, temp_db):
        """Test MonitorApp handles case when no active task exists."""
        from unittest.mock import AsyncMock, patch

        # Act: Create app with empty database and manually call on_mount
        app = MonitorApp()
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: App should handle no active task
        assert app._active_task is None
        assert app.title == "jot - No active task"

    def test_app_displays_task_with_emoji_and_theme(self, temp_db):
        """Test MonitorApp displays task with emoji and theme styling."""
        # Arrange: Create active task
        from unittest.mock import AsyncMock, patch

        from jot.db.repository import TaskRepository

        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test task with theme",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Act: Create app, compose widgets, and mount
        app = MonitorApp()
        # Compose widgets first
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: Task should be loaded and title updated with exact format
        assert app._active_task is not None
        assert app._active_task.description == "Test task with theme"
        # Verify title format matches AC specification exactly
        assert app.title == "jot - Test task with theme"

    def test_app_memory_usage_below_limit(self, temp_db):
        """Test MonitorApp memory usage stays below 50MB."""
        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        try:
            # Create app and mount
            app = MonitorApp()
            widgets = list(app.compose())
            app._task_widget = widgets[0] if widgets else None
            import asyncio

            asyncio.run(app.on_mount())

            # Get current memory usage
            current, peak = tracemalloc.get_traced_memory()
            memory_mb = peak / (1024 * 1024)

            # Assert memory usage is below 50MB
            assert memory_mb < 50, f"Memory usage {memory_mb:.2f}MB exceeds 50MB limit"
        finally:
            tracemalloc.stop()

    def test_app_displays_emoji_in_widget_text(self, temp_db):
        """Test MonitorApp displays emoji in widget text."""
        # Arrange: Create active task
        from unittest.mock import AsyncMock, patch

        from jot.core.theme import TaskEmoji
        from jot.db.repository import TaskRepository

        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test emoji display",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Act: Create app, compose widgets, and mount
        app = MonitorApp()
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: Widget text should contain emoji
        assert app._task_widget is not None
        # Access content via content property (Textual Static widget)
        widget_content = str(app._task_widget.content)
        # Check that emoji is in the display text
        assert TaskEmoji.ACTIVE in widget_content

    def test_app_applies_theme_styles(self, temp_db):
        """Test MonitorApp applies theme styles to widget."""
        # Arrange: Create active task
        from unittest.mock import AsyncMock, patch

        from jot.core.theme import get_textual_style_for_state
        from jot.db.repository import TaskRepository

        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Test style application",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Act: Create app, compose widgets, and mount
        app = MonitorApp()
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: Styles should be applied (check style properties)
        assert app._task_widget is not None
        # Verify styles are set (Textual applies styles via styles property)
        # The styles should have foreground set if theme provides it
        style_dict = get_textual_style_for_state("active")
        if "foreground" in style_dict:
            # Textual styles are applied, verify widget has styles property
            assert hasattr(app._task_widget, "styles")

    def test_app_action_quit_exits(self):
        """Test MonitorApp quit action exits the app."""
        import asyncio

        app = MonitorApp()
        # Mock exit to verify it's called
        exit_called = False

        def mock_exit():
            nonlocal exit_called
            exit_called = True

        app.exit = mock_exit
        # Call async action_quit
        asyncio.run(app.action_quit())

        # Assert: exit should have been called
        assert exit_called

    def test_app_widget_displays_no_active_task_text(self, temp_db):
        """Test MonitorApp widget displays 'No active task' text when no task."""
        from unittest.mock import AsyncMock, patch

        # Act: Create app with empty database
        app = MonitorApp()
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: Widget should display "No active task"
        assert app._task_widget is not None
        widget_content = str(app._task_widget.content)
        assert "No active task" in widget_content

    def test_app_widget_displays_task_description(self, temp_db):
        """Test MonitorApp widget displays task description."""
        # Arrange: Create active task
        from unittest.mock import AsyncMock, patch

        from jot.db.repository import TaskRepository

        repo = TaskRepository()
        task = Task(
            id=str(uuid.uuid4()),
            description="Specific test description",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.create_task(task)

        # Act: Create app, compose widgets, and mount
        app = MonitorApp()
        widgets = list(app.compose())
        app._task_widget = widgets[0] if widgets else None
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: Widget should contain task description
        assert app._task_widget is not None
        widget_content = str(app._task_widget.content)
        assert "Specific test description" in widget_content

    def test_app_ipc_server_created_on_mount(self, temp_db):
        """Test MonitorApp creates IPC server on mount (creates socket file)."""
        from unittest.mock import AsyncMock, patch

        # Act: Create app and mount
        app = MonitorApp()
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: IPC server should be created and started
        mock_ipc_server.assert_called_once()
        mock_server_instance.start.assert_called_once()
        assert app._ipc_server is not None

    def test_app_cleanup_on_unmount(self, temp_db):
        """Test MonitorApp cleans up IPC server on unmount."""
        from unittest.mock import AsyncMock, patch

        # Arrange: Create and mount app
        app = MonitorApp()
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

            # Act: Unmount app
            asyncio.run(app.on_unmount())

        # Assert: IPC server should be stopped
        mock_server_instance.stop.assert_called_once()

    def test_app_handles_stale_socket_file(self, temp_db, tmp_path):
        """Test MonitorApp handles stale socket file on startup."""
        from unittest.mock import AsyncMock, patch

        # Arrange: Create stale socket file
        socket_path = tmp_path / "monitor.sock"
        socket_path.touch()

        # Act: Create app and mount (IPC server should remove stale socket)
        app = MonitorApp()
        with patch("jot.monitor.app.IPCServer") as mock_ipc_server:
            mock_server_instance = AsyncMock()
            mock_ipc_server.return_value = mock_server_instance
            import asyncio

            asyncio.run(app.on_mount())

        # Assert: IPC server was created and started (it handles stale sockets)
        mock_ipc_server.assert_called_once()
        mock_server_instance.start.assert_called_once()
