"""Comprehensive test suite for config.paths module.

This test suite achieves 100% code coverage for the XDG path resolution module,
testing all platform-specific behaviors, environment variable overrides,
directory creation, permissions, and error handling.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jot.config.paths import (
    _ensure_directory,
    _get_env_path,
    _is_windows,
    _is_wsl,
    get_config_dir,
    get_data_dir,
    get_runtime_dir,
)


class TestPlatformDetection:
    """Test platform detection utilities."""

    def test_is_windows_on_windows(self):
        """Test Windows detection on Windows platform."""
        with patch("sys.platform", "win32"):
            assert _is_windows() is True

    def test_is_windows_on_linux(self):
        """Test Windows detection on Linux platform."""
        with patch("sys.platform", "linux"):
            assert _is_windows() is False

    def test_is_windows_on_darwin(self):
        """Test Windows detection on macOS platform."""
        with patch("sys.platform", "darwin"):
            assert _is_windows() is False

    def test_is_wsl_detection(self):
        """Test WSL detection via platform.uname().release."""
        mock_uname = MagicMock()
        mock_uname.release = "5.10.16.3-microsoft-standard-WSL2"

        with patch("platform.uname", return_value=mock_uname):
            assert _is_wsl() is True

    def test_is_not_wsl_detection(self):
        """Test WSL detection returns False on regular Linux."""
        mock_uname = MagicMock()
        mock_uname.release = "5.15.0-56-generic"

        with patch("platform.uname", return_value=mock_uname):
            assert _is_wsl() is False


class TestEnvPathHelper:
    """Test _get_env_path helper function."""

    def test_get_env_path_when_set(self, monkeypatch, tmp_path):
        """Test _get_env_path returns Path when environment variable is set."""
        test_path = tmp_path / "custom"
        monkeypatch.setenv("TEST_VAR", str(test_path))

        result = _get_env_path("TEST_VAR")

        assert result == test_path

    def test_get_env_path_with_tilde(self, monkeypatch, tmp_path):
        """Test _get_env_path expands tilde in path."""
        monkeypatch.setenv("TEST_VAR", "~/custom")

        result = _get_env_path("TEST_VAR")

        assert result == Path.home() / "custom"

    def test_get_env_path_when_not_set(self, monkeypatch):
        """Test _get_env_path returns default when variable not set."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        default = Path("/default/path")

        result = _get_env_path("TEST_VAR", default)

        assert result == default

    def test_get_env_path_none_default(self, monkeypatch):
        """Test _get_env_path returns None when no default provided."""
        monkeypatch.delenv("TEST_VAR", raising=False)

        result = _get_env_path("TEST_VAR")

        assert result is None


class TestEnsureDirectory:
    """Test _ensure_directory helper function."""

    def test_create_directory_when_not_exists(self, tmp_path):
        """Test _ensure_directory creates directory when it doesn't exist."""
        new_dir = tmp_path / "new_directory"

        result = _ensure_directory(new_dir)

        assert result == new_dir
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_directory_with_parents(self, tmp_path):
        """Test _ensure_directory creates parent directories."""
        nested_dir = tmp_path / "parent" / "child" / "grandchild"

        result = _ensure_directory(nested_dir)

        assert result == nested_dir
        assert nested_dir.exists()

    def test_directory_already_exists(self, tmp_path):
        """Test _ensure_directory is idempotent when directory exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        result = _ensure_directory(existing_dir)

        assert result == existing_dir
        assert existing_dir.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
    def test_directory_permissions_unix(self, tmp_path):
        """Test _ensure_directory sets 0700 permissions on Unix."""
        new_dir = tmp_path / "restricted"

        _ensure_directory(new_dir, mode=0o700)

        # Check permissions (mask with 0o777 to ignore file type bits)
        actual_mode = new_dir.stat().st_mode & 0o777
        assert actual_mode == 0o700

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
    def test_directory_permissions_enforced_on_existing(self, tmp_path):
        """Test _ensure_directory enforces permissions on existing directory."""
        existing_dir = tmp_path / "existing_permissive"
        existing_dir.mkdir(mode=0o755)  # Start with permissive

        _ensure_directory(existing_dir, mode=0o700)

        actual_mode = existing_dir.stat().st_mode & 0o777
        assert actual_mode == 0o700

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_directory_no_chmod_on_windows(self, tmp_path):
        """Test _ensure_directory doesn't call chmod on Windows."""
        new_dir = tmp_path / "windows_dir"

        # Should not raise error even though Windows doesn't support Unix permissions
        result = _ensure_directory(new_dir, mode=0o700)

        assert result.exists()


class TestConfigDir:
    """Test get_config_dir() function."""

    @pytest.fixture
    def clean_env(self, monkeypatch):
        """Remove all XDG environment variables."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.delenv("TEMP", raising=False)

    @pytest.fixture
    def mock_home(self, tmp_path, monkeypatch):
        """Set up temporary home directory."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home)
        return home

    def test_default_config_dir_linux(self, clean_env, mock_home, monkeypatch):
        """Test default config directory on Linux."""
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        assert config_dir == mock_home / ".config" / "jot"
        assert config_dir.exists()

    def test_default_config_dir_darwin(self, clean_env, mock_home, monkeypatch):
        """Test default config directory on macOS."""
        monkeypatch.setattr("sys.platform", "darwin")

        config_dir = get_config_dir()

        assert config_dir == mock_home / ".config" / "jot"
        assert config_dir.exists()

    def test_xdg_config_home_override(self, clean_env, mock_home, monkeypatch):
        """Test XDG_CONFIG_HOME environment variable override."""
        custom_config = mock_home / "custom_config"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        assert config_dir == custom_config / "jot"
        assert config_dir.exists()

    def test_xdg_config_home_with_tilde(self, clean_env, monkeypatch):
        """Test XDG_CONFIG_HOME with tilde expansion."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "~/.my_config")
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        expected = Path.home() / ".my_config" / "jot"
        assert config_dir == expected
        assert config_dir.exists()

    def test_windows_config_dir(self, clean_env, tmp_path, monkeypatch):
        """Test config directory on Windows."""
        appdata = tmp_path / "AppData" / "Roaming"
        appdata.mkdir(parents=True)
        monkeypatch.setenv("APPDATA", str(appdata))
        monkeypatch.setattr("sys.platform", "win32")

        config_dir = get_config_dir()

        assert config_dir == appdata / "jot"
        assert config_dir.exists()

    def test_windows_config_dir_missing_appdata(self, clean_env, monkeypatch):
        """Test error when APPDATA is missing on Windows."""
        monkeypatch.setattr("sys.platform", "win32")

        with pytest.raises(OSError, match="APPDATA environment variable not set"):
            get_config_dir()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
    def test_config_dir_has_restricted_permissions(self, clean_env, mock_home, monkeypatch):
        """Test config directory is created with 0700 permissions."""
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        actual_mode = config_dir.stat().st_mode & 0o777
        assert actual_mode == 0o700


class TestDataDir:
    """Test get_data_dir() function."""

    @pytest.fixture
    def clean_env(self, monkeypatch):
        """Remove all XDG environment variables."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.delenv("TEMP", raising=False)

    @pytest.fixture
    def mock_home(self, tmp_path, monkeypatch):
        """Set up temporary home directory."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home)
        return home

    def test_default_data_dir_linux(self, clean_env, mock_home, monkeypatch):
        """Test default data directory on Linux."""
        monkeypatch.setattr("sys.platform", "linux")

        data_dir = get_data_dir()

        assert data_dir == mock_home / ".local" / "share" / "jot"
        assert data_dir.exists()

    def test_default_data_dir_darwin(self, clean_env, mock_home, monkeypatch):
        """Test default data directory on macOS."""
        monkeypatch.setattr("sys.platform", "darwin")

        data_dir = get_data_dir()

        assert data_dir == mock_home / ".local" / "share" / "jot"
        assert data_dir.exists()

    def test_xdg_data_home_override(self, clean_env, mock_home, monkeypatch):
        """Test XDG_DATA_HOME environment variable override."""
        custom_data = mock_home / "custom_data"
        monkeypatch.setenv("XDG_DATA_HOME", str(custom_data))
        monkeypatch.setattr("sys.platform", "linux")

        data_dir = get_data_dir()

        assert data_dir == custom_data / "jot"
        assert data_dir.exists()

    def test_xdg_data_home_with_tilde(self, clean_env, monkeypatch):
        """Test XDG_DATA_HOME with tilde expansion."""
        monkeypatch.setenv("XDG_DATA_HOME", "~/.my_data")
        monkeypatch.setattr("sys.platform", "linux")

        data_dir = get_data_dir()

        expected = Path.home() / ".my_data" / "jot"
        assert data_dir == expected
        assert data_dir.exists()

    def test_windows_data_dir(self, clean_env, tmp_path, monkeypatch):
        """Test data directory on Windows."""
        localappdata = tmp_path / "AppData" / "Local"
        localappdata.mkdir(parents=True)
        monkeypatch.setenv("LOCALAPPDATA", str(localappdata))
        monkeypatch.setattr("sys.platform", "win32")

        data_dir = get_data_dir()

        assert data_dir == localappdata / "jot"
        assert data_dir.exists()

    def test_windows_data_dir_missing_localappdata(self, clean_env, monkeypatch):
        """Test error when LOCALAPPDATA is missing on Windows."""
        monkeypatch.setattr("sys.platform", "win32")

        with pytest.raises(OSError, match="LOCALAPPDATA environment variable not set"):
            get_data_dir()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
    def test_data_dir_has_restricted_permissions(self, clean_env, mock_home, monkeypatch):
        """Test data directory is created with 0700 permissions."""
        monkeypatch.setattr("sys.platform", "linux")

        data_dir = get_data_dir()

        actual_mode = data_dir.stat().st_mode & 0o777
        assert actual_mode == 0o700


class TestRuntimeDir:
    """Test get_runtime_dir() function."""

    @pytest.fixture
    def clean_env(self, monkeypatch):
        """Remove all XDG environment variables."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        monkeypatch.delenv("APPDATA", raising=False)
        monkeypatch.delenv("LOCALAPPDATA", raising=False)
        monkeypatch.delenv("TEMP", raising=False)

    @pytest.fixture
    def mock_home(self, tmp_path, monkeypatch):
        """Set up temporary home directory."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home)
        return home

    def test_xdg_runtime_dir_set(self, clean_env, tmp_path, monkeypatch):
        """Test runtime dir when XDG_RUNTIME_DIR is set."""
        runtime_base = tmp_path / "run"
        runtime_base.mkdir()
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime_base))
        monkeypatch.setattr("sys.platform", "linux")

        runtime_dir = get_runtime_dir()

        assert runtime_dir == runtime_base / "jot"
        assert runtime_dir.exists()

    def test_runtime_dir_fallback_to_data_dir(self, clean_env, mock_home, monkeypatch):
        """Test runtime dir fallback when XDG_RUNTIME_DIR not set."""
        monkeypatch.setattr("sys.platform", "linux")

        runtime_dir = get_runtime_dir()
        data_dir = get_data_dir()

        # Should fallback to data directory
        assert runtime_dir == data_dir
        assert runtime_dir.exists()

    def test_xdg_runtime_dir_with_tilde(self, clean_env, monkeypatch):
        """Test XDG_RUNTIME_DIR with tilde expansion."""
        monkeypatch.setenv("XDG_RUNTIME_DIR", "~/my_runtime")
        monkeypatch.setattr("sys.platform", "linux")

        runtime_dir = get_runtime_dir()

        expected = Path.home() / "my_runtime" / "jot"
        assert runtime_dir == expected
        assert runtime_dir.exists()

    def test_windows_runtime_dir(self, clean_env, tmp_path, monkeypatch):
        """Test runtime directory on Windows."""
        temp_dir = tmp_path / "Temp"
        temp_dir.mkdir()
        monkeypatch.setenv("TEMP", str(temp_dir))
        monkeypatch.setattr("sys.platform", "win32")

        runtime_dir = get_runtime_dir()

        assert runtime_dir == temp_dir / "jot"
        assert runtime_dir.exists()

    def test_windows_runtime_dir_missing_temp(self, clean_env, monkeypatch):
        """Test error when TEMP is missing on Windows."""
        monkeypatch.setattr("sys.platform", "win32")

        with pytest.raises(OSError, match="TEMP environment variable not set"):
            get_runtime_dir()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix permissions test")
    def test_runtime_dir_has_restricted_permissions(self, clean_env, tmp_path, monkeypatch):
        """Test runtime directory is created with 0700 permissions."""
        runtime_base = tmp_path / "run"
        runtime_base.mkdir()
        monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime_base))
        monkeypatch.setattr("sys.platform", "linux")

        runtime_dir = get_runtime_dir()

        actual_mode = runtime_dir.stat().st_mode & 0o777
        assert actual_mode == 0o700


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.fixture
    def clean_env(self, monkeypatch):
        """Remove all XDG environment variables."""
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)

    @pytest.fixture
    def mock_home(self, tmp_path, monkeypatch):
        """Set up temporary home directory."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: home)
        return home

    def test_paths_with_spaces(self, clean_env, tmp_path, monkeypatch):
        """Test paths with spaces are handled correctly."""
        custom_config = tmp_path / "my config dir"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        assert config_dir == custom_config / "jot"
        assert config_dir.exists()

    def test_paths_with_unicode(self, clean_env, tmp_path, monkeypatch):
        """Test paths with unicode characters."""
        custom_data = tmp_path / "données_utilisateur"
        monkeypatch.setenv("XDG_DATA_HOME", str(custom_data))
        monkeypatch.setattr("sys.platform", "linux")

        data_dir = get_data_dir()

        assert data_dir == custom_data / "jot"
        assert data_dir.exists()

    def test_multiple_calls_are_idempotent(self, clean_env, mock_home, monkeypatch):
        """Test multiple calls to the same function are idempotent."""
        monkeypatch.setattr("sys.platform", "linux")

        # Call multiple times
        dir1 = get_config_dir()
        dir2 = get_config_dir()
        dir3 = get_config_dir()

        # All should return the same path and directory should still exist
        assert dir1 == dir2 == dir3
        assert dir1.exists()

    def test_empty_string_env_var_uses_default(self, clean_env, mock_home, monkeypatch):
        """Test empty string environment variable falls back to default."""
        monkeypatch.setenv("XDG_CONFIG_HOME", "")
        monkeypatch.setattr("sys.platform", "linux")

        config_dir = get_config_dir()

        # Should use default, not empty string
        assert config_dir == mock_home / ".config" / "jot"
        assert config_dir.exists()

    def test_simultaneous_directory_creation(self, clean_env, mock_home, monkeypatch, tmp_path):
        """Test concurrent-like calls don't cause issues (exist_ok=True validation)."""
        monkeypatch.setattr("sys.platform", "linux")

        # Get config dir which creates it
        config_dir1 = get_config_dir()

        # Try to create it again manually then call function
        config_dir1.rmdir()  # Remove it first
        config_dir2 = get_config_dir()  # Should recreate without error

        assert config_dir1 == config_dir2
        assert config_dir2.exists()
