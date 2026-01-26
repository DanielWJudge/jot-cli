"""Path resolution utilities following XDG Base Directory specification.

This module provides platform-aware path resolution for jot's configuration,
data, and runtime directories. It respects XDG environment variables on
Linux/macOS and uses appropriate Windows equivalents on Windows platforms.

All paths are created with restrictive permissions (0700) if they don't exist.

IMPORTANT: This module MUST use only stdlib - NO external dependencies allowed.
This is the foundation layer of the architecture.
"""

import os
import platform
import sys
from pathlib import Path


def _is_windows() -> bool:
    """Check if running on Windows (not WSL).

    Returns:
        bool: True if running on native Windows, False otherwise.
    """
    return sys.platform == "win32"


def _is_wsl() -> bool:
    """Check if running on Windows Subsystem for Linux.

    Returns:
        bool: True if running in WSL, False otherwise.
    """
    return "microsoft" in platform.uname().release.lower()


def _get_env_path(var_name: str, default: Path | None = None) -> Path | None:
    """Get path from environment variable with tilde expansion.

    Args:
        var_name: Name of the environment variable to read.
        default: Default path to return if variable not set or empty.

    Returns:
        Path from environment variable (expanded), default, or None.
    """
    value = os.environ.get(var_name)
    if value:
        return Path(value).expanduser()
    return default


def _ensure_directory(path: Path, mode: int = 0o700) -> Path:
    """Create directory with specified permissions if it doesn't exist.

    On Unix systems, enforces the specified permission mode even if the
    directory already exists. On Windows, permissions are handled by the OS.

    Args:
        path: Directory path to create.
        mode: Unix permission bits (default: 0o700 - owner only).

    Returns:
        Path: The created/existing directory path.

    Raises:
        OSError: If directory cannot be created or accessed.
    """
    path.mkdir(parents=True, exist_ok=True, mode=mode)

    # Enforce permissions on Unix (mkdir mode can be affected by umask)
    if not _is_windows():
        path.chmod(mode)

    return path


def get_config_dir() -> Path:
    """Get the jot configuration directory.

    Returns XDG_CONFIG_HOME/jot on Linux/macOS, %APPDATA%/jot on Windows.
    Creates directory with 0700 permissions if it doesn't exist.
    Respects XDG_CONFIG_HOME environment variable override.

    Returns:
        Path: Absolute path to config directory.

    Raises:
        OSError: If directory cannot be created or accessed, or if required
                 Windows environment variables are not set.
    """
    if _is_windows():
        # Windows: %APPDATA%/jot
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise OSError("APPDATA environment variable not set")
        config_dir = Path(appdata) / "jot"
    else:
        # Linux/macOS: XDG_CONFIG_HOME/jot or ~/.config/jot
        default = Path.home() / ".config"
        config_home = _get_env_path("XDG_CONFIG_HOME", default)
        if config_home is None:
            config_home = default
        config_dir = config_home / "jot"

    return _ensure_directory(config_dir)


def get_data_dir() -> Path:
    """Get the jot data directory.

    Returns XDG_DATA_HOME/jot on Linux/macOS, %LOCALAPPDATA%/jot on Windows.
    Creates directory with 0700 permissions if it doesn't exist.
    Respects XDG_DATA_HOME environment variable override.

    Returns:
        Path: Absolute path to data directory.

    Raises:
        OSError: If directory cannot be created or accessed, or if required
                 Windows environment variables are not set.
    """
    if _is_windows():
        # Windows: %LOCALAPPDATA%/jot
        local_appdata = os.environ.get("LOCALAPPDATA")
        if not local_appdata:
            raise OSError("LOCALAPPDATA environment variable not set")
        data_dir = Path(local_appdata) / "jot"
    else:
        # Linux/macOS: XDG_DATA_HOME/jot or ~/.local/share/jot
        default = Path.home() / ".local" / "share"
        data_home = _get_env_path("XDG_DATA_HOME", default)
        if data_home is None:
            data_home = default
        data_dir = data_home / "jot"

    return _ensure_directory(data_dir)


def get_runtime_dir() -> Path:
    """Get the jot runtime directory.

    Returns XDG_RUNTIME_DIR/jot on Linux/macOS with fallback.
    Falls back to XDG_DATA_HOME/jot if XDG_RUNTIME_DIR not set.
    On Windows, returns %TEMP%/jot.
    Creates directory with 0700 permissions if it doesn't exist.

    Returns:
        Path: Absolute path to runtime directory.

    Raises:
        OSError: If directory cannot be created or accessed, or if required
                 Windows environment variables are not set.
    """
    if _is_windows():
        # Windows: %TEMP%/jot
        temp = os.environ.get("TEMP")
        if not temp:
            raise OSError("TEMP environment variable not set")
        runtime_dir = Path(temp) / "jot"
    else:
        # Linux/macOS: Try XDG_RUNTIME_DIR first, fallback to data dir
        runtime_base = _get_env_path("XDG_RUNTIME_DIR")
        runtime_dir = runtime_base / "jot" if runtime_base else get_data_dir()

    return _ensure_directory(runtime_dir)
