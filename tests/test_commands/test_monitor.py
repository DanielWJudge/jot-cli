"""Test suite for monitor command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from jot.cli import app


class TestMonitorCommand:
    """Test jot monitor command."""

    def test_monitor_launches_when_not_running(self, temp_db, tmp_path: Path):
        """Test monitor command launches app when not already running."""
        runner = CliRunner()

        # Mock get_runtime_dir to return tmp_path and MonitorApp.run to avoid launching Textual
        with (
            patch("jot.cli.get_runtime_dir", return_value=tmp_path),
            patch("jot.cli.MonitorApp.run") as mock_run,
        ):
            result = runner.invoke(app, ["monitor"])

            # Should attempt to run the app
            assert mock_run.called
            assert result.exit_code == 0

    def test_monitor_detects_already_running(self, temp_db, tmp_path: Path):
        """Test monitor command detects already running instance."""
        runner = CliRunner()

        # Create socket file to simulate running monitor
        socket_path = tmp_path / "monitor.sock"
        socket_path.touch()

        with patch("jot.cli.get_runtime_dir", return_value=tmp_path):
            result = runner.invoke(app, ["monitor"])

            assert result.exit_code == 0
            assert "already running" in result.stdout.lower()
            assert "Monitor is already running" in result.stdout
